#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Literal, NewType, Optional, TypedDict, Union, get_args

import cwl_utils.parser as cwl_parser
import networkx as nx
from pipe import map

DockerImage = NewType("DockerImage", str)
Output = NewType("Output", str)
Binding = NewType("Binding", Dict[str, "WorkflowElement"])


#  @dataclass
#  class Provenance:
#      target: Path
#      command: str
#      params: Dict
#      parent: "Provenance" = None
#


class Workflow(abc.ABC):
    @abc.abstractmethod
    def inputs(self, name: str = None) -> Union["InOut", List["InOut"]]:
        ...

    @abc.abstractmethod
    def outputs(self, name: str = None) -> Union["InOut", List["InOut"]]:
        ...

    @abc.abstractmethod
    def steps(self, name: str = None) -> Union["WorkflowStep", List["WorkflowStep"]]:
        ...

    @abc.abstractmethod
    def nodes(
        self, name: str = None
    ) -> Union["WorkflowElement", List["WorkflowElement"]]:
        ...


class WorkflowElement(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def in_binding(self) -> Binding:
        ...

    @property
    @abc.abstractmethod
    def out_binding(self) -> Binding:
        ...

    @property
    @abc.abstractmethod
    def workflow(self) -> Workflow:
        ...

    def __repr__(self):
        return f"<{self.name}>"

    def __eq__(self, other):
        return self.name == other.name


class InOut(WorkflowElement, abc.ABC):
    @abc.abstractmethod
    def is_input(self) -> bool:
        ...

    def is_output(self) -> bool:
        ...


class WorkflowStep(WorkflowElement):
    @property
    @abc.abstractmethod
    def in_binding(self) -> Binding:
        ...

    @property
    @abc.abstractmethod
    def out_binding(self) -> Binding:
        ...

    @property
    @abc.abstractmethod
    def command(self) -> Union[str, None]:
        ...

    @property
    @abc.abstractmethod
    def docker_image(self) -> Union[str, None]:
        ...


class NXWorkflow(Workflow):
    def __init__(self, dag: nx.DiGraph):
        self._dag = dag
        self._outputs: Dict[str, InOut] = None
        self._inputs: Dict[str, InOut] = None
        self._steps: Dict[str, WorkflowStep] = None

    def outputs(self, name: str = None) -> Union["InOut", List["InOut"]]:
        if self._outputs is None:
            self._outputs = {
                node: NXInOut(node, self._dag)
                for node in self._dag.nodes
                if self._dag.out_degree(node) == 0
            }

        if name:
            return self._outputs[name]
        return list(self._outputs.values())

    def inputs(self, name: str = None) -> Union["InOut", List["InOut"]]:
        if self._inputs is None:
            self._inputs = {
                node: NXInOut(node, self._dag)
                for node in self._dag.nodes
                if self._dag.in_degree(node) == 0
            }
        if name:
            return self._inputs[name]
        return list(self._inputs.values())

    def steps(self, name: str = None) -> Union["WorkflowStep", List["WorkflowStep"]]:
        if self._steps is None:
            self._steps = {
                node: NXWorkflowStep(node, self._dag)
                for node, data in self._dag.nodes(data=True)
                if data.get("type") == "step"
            }
        if name:
            return self._steps[name]
        return list(self._steps.values())

    def nodes(
        self, name: str = None
    ) -> Union["WorkflowElement", List["WorkflowElement"]]:
        nodes = {
            node: NXWorkflowStep(node, self._dag)
            if data.get("type") == "step"
            else NXInOut(node, self._dag)
            for node, data in self._dag.nodes(data=True)
        }
        if name:
            return nodes[name]
        return list(nodes.values())


class NXWorkflowElement(WorkflowElement):
    def __init__(self, name: str, dag: nx.DiGraph):
        self._name = name
        self._dag = dag
        self._node = dag.nodes[name]

    @property
    def name(self) -> str:
        return self._name

    @property
    def workflow(self) -> Workflow:
        return NXWorkflow(self._dag)

    @property
    def in_binding(self) -> Binding:
        binding: Binding = {}
        for edge in self._dag.in_edges(self.name, data=True):
            start, _, data = edge
            label = data["label"].split("/")[1]
            self._add_binding(binding, label, start)
        return binding

    @property
    def out_binding(self) -> Binding:
        binding: Binding = {}
        for edge in self._dag.edges(self.name, data=True):
            _, end, data = edge
            label = data["label"].split("/")[1]
            self._add_binding(binding, label, end)
        return binding

    @abc.abstractmethod
    def _add_binding(self, binding: Binding, label: str, node: str):
        ...


class NXInOut(InOut, NXWorkflowElement):
    def _add_binding(self, binding: Binding, label: str, node: str):
        binding[label] = NXWorkflowStep(node, self._dag)

    def is_input(self) -> bool:
        return len(self._dag.in_edges(self.name)) == 0

    def is_output(self) -> bool:
        return len(self._dag.out_edges(self.name)) == 0


class NXWorkflowStep(NXWorkflowElement, WorkflowStep):
    def _add_binding(self, binding: Binding, label: str, node: str):
        binding[label] = NXInOut(node, self._dag)

    @property
    def command(self) -> Union[str, None]:
        return self._node.get("command")

    @property
    def docker_image(self) -> Union[str, None]:
        return self._node.get("docker_image")


class WorkflowFactory(abc.ABC):
    @abc.abstractmethod
    def get(self):
        ...


CWLElement = Literal["inputs", "outpus", "steps"]


@dataclass
class NXWorkflowFactory(WorkflowFactory):
    cwl_workflow: cwl_parser.Workflow

    def get(self) -> Workflow:
        dag = self._get_dag()
        return NXWorkflow(dag)

    def _get_dag(self) -> nx.DiGraph:
        dag = nx.DiGraph()
        inputs = list(self.cwl_workflow.inputs | map(lambda x: self._get_id(x.id)))
        outputs = list(self.cwl_workflow.outputs | map(lambda x: self._get_id(x.id)))
        dag.add_nodes_from(inputs + outputs, type="inout")

        for step in self.cwl_workflow.steps:
            step_id = self._get_id(step.id)
            docker_image = self._get_docker_image(step)
            dag.add_node(
                step_id,
                type="step",
                command=step.run.baseCommand,
                docker_image=docker_image,
            )

            for in_ in step.in_:
                dag.add_edge(
                    self._get_id(in_.source), step_id, label=self._get_id(in_.id)
                )
            for out in step.out:
                dest_node = out
                for cwl_out in self.cwl_workflow.outputs:
                    if cwl_out.outputSource == out:
                        dest_node = cwl_out.id
                        break
                dag.add_edge(step_id, self._get_id(dest_node), label=self._get_id(out))

        return dag

    def _get_element_by_id(
        self, cwl_element: CWLElement, _id: str
    ) -> cwl_parser.WorkflowStep:
        return list(
            filter(lambda s: s.id == _id, getattr(self.cwl_workflow, cwl_element))
        )[0]

    def _get_id(self, element) -> str:
        return element.split("#")[1] if "#" in element else element

    def _get_docker_image(self, step) -> Union[str, None]:
        for req in step.run.requirements:
            if isinstance(req, get_args(cwl_parser.DockerRequirement)):
                return req.dockerPull


Input = Union[str, int, float, "Artefact", None]


@dataclass
class Artefact:
    name: str
    workflow_step: WorkflowStep
    inputs: Dict[str, Input]
    command: Optional[str]
    docker_img: Optional[str]


@dataclass
class ArtefactFactory:
    worflow: Workflow
    params: Dict

    def get(self, name: str = None) -> Union[Artefact, List[Artefact]]:
        artefacts = {}
        outputs = self.worflow.outputs() if name is None else [self.worflow.nodes(name)]
        for output in outputs:
            self._get(output, artefacts)

        return list(artefacts.values()) if name is None else artefacts[name]

    def _get(self, inout: InOut, artefacts: Dict[str, Artefact]):
        artefact_name = inout.name
        workflow_step = list(inout.in_binding.values())[0]
        inputs = {}
        for binding, node in workflow_step.in_binding.items():
            if node.is_input():
                inputs[binding] = self.params.get(node.name)
            else:
                try:
                    intermediate_artefact = artefacts[node.name]
                except KeyError:
                    self._get(node, artefacts)
                    inputs[binding] = artefacts[node.name]

        artefact = Artefact(artefact_name, workflow_step, inputs)
        artefacts[inout.name] = artefact
