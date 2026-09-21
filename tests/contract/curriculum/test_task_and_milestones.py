"""Contract tests for Practical Tasks and Project Milestones (S5.4)."""

import pytest
from pydantic import ValidationError

from study_engine.curriculum.milestone_contracts import (
    MilestoneStatus,
    ProjectMilestone,
    ProjectSpecification,
)
from study_engine.curriculum.task_contracts import (
    LabEnvironmentRequirements,
    PracticalTaskSpecification,
    TaskDifficulty,
)


def test_milestone_status_has_zero_transition_authority() -> None:
    """HG-S5.4-06: S5.4 defines vocabulary; possesses no transition methods."""
    assert len(MilestoneStatus) == 5
    assert set(MilestoneStatus) == {
        MilestoneStatus.PENDING,
        MilestoneStatus.IN_PROGRESS,
        MilestoneStatus.SUBMITTED,
        MilestoneStatus.SATISFIED,
        MilestoneStatus.FAILED,
    }

    # Verify no state transition methods exist on the enum or its members
    for status in MilestoneStatus:
        assert not hasattr(status, "transition_to")
        assert not hasattr(status, "advance")
        assert not hasattr(status, "set_status")
        assert not hasattr(status, "mutate")


def test_project_milestone_dag_cycle_detected_and_rejected() -> None:
    """Cyclic milestone dependencies must be detected and rejected."""
    m1 = ProjectMilestone(
        milestone_id="m1",
        project_id="proj-cyc",
        sequence_order=0,
        title="M1",
        description="D1",
        prerequisite_milestone_ids=("m2",),  # Cycle: m1 -> m2 -> m1
    )
    m2 = ProjectMilestone(
        milestone_id="m2",
        project_id="proj-cyc",
        sequence_order=1,
        title="M2",
        description="D2",
        prerequisite_milestone_ids=("m1",),
    )

    with pytest.raises(
        ValidationError, match="Cyclic milestone dependency"
    ):
        ProjectSpecification(
            project_id="proj-cyc",
            title="Cyclic Project",
            curriculum_node_id="node-01",
            milestones=(m1, m2),
        )


def test_project_milestone_self_prerequisite_rejected() -> None:
    """Milestone cannot depend on itself."""
    m1 = ProjectMilestone(
        milestone_id="m1",
        project_id="proj-self",
        sequence_order=0,
        title="M1",
        description="D1",
        prerequisite_milestone_ids=("m1",),
    )

    with pytest.raises(
        ValidationError, match="cannot depend on itself"
    ):
        ProjectSpecification(
            project_id="proj-self",
            title="Self Prereq Project",
            curriculum_node_id="node-01",
            milestones=(m1,),
        )


def test_project_milestone_unknown_prerequisite_rejected() -> None:
    """Milestone cannot reference a prerequisite not in the project."""
    m1 = ProjectMilestone(
        milestone_id="m1",
        project_id="proj-unk",
        sequence_order=0,
        title="M1",
        description="D1",
        prerequisite_milestone_ids=("m-nonexistent",),
    )

    with pytest.raises(
        ValidationError, match="references unknown prerequisite"
    ):
        ProjectSpecification(
            project_id="proj-unk",
            title="Unknown Prereq Project",
            curriculum_node_id="node-01",
            milestones=(m1,),
        )


def test_p0_detector_fuerza_bruta_milestones_representation() -> None:
    """Demonstrate representation of P0 (Detector incremental, 3 entregas)."""
    m0 = ProjectMilestone(
        milestone_id="p0-m1-baseline",
        project_id="P0",
        sequence_order=0,
        title="Entrega 1: Parser básico + contador de intentos fallidos",
        description="Parsea auth.log y cuenta IPs con > N fallos",
        prerequisite_milestone_ids=(),
    )
    m1 = ProjectMilestone(
        milestone_id="p0-m2-sliding-window",
        project_id="P0",
        sequence_order=1,
        title="Entrega 2: Ventana deslizante (deque) + complejidad O(1)",
        description="Reemplaza ventana fija por collections.deque",
        prerequisite_milestone_ids=("p0-m1-baseline",),
    )
    m2 = ProjectMilestone(
        milestone_id="p0-m3-full-cli",
        project_id="P0",
        sequence_order=2,
        title="Entrega 3: CLI completa + export JSON + 10 tests",
        description="Integra argparse, whitelist, tests con 10k eventos",
        prerequisite_milestone_ids=("p0-m2-sliding-window",),
    )

    proj = ProjectSpecification(
        project_id="P0",
        title="P0: Detector de Fuerza Bruta Incremental",
        curriculum_node_id="node-f0-p0",
        milestones=(m0, m1, m2),
        capstone_gateway_id="G0.2",
    )

    assert proj.project_id == "P0"
    assert len(proj.milestones) == 3
    assert proj.capstone_gateway_id == "G0.2"


def test_practical_task_specification() -> None:
    """Verify PracticalTaskSpecification and LabEnvironmentRequirements."""
    env = LabEnvironmentRequirements(
        environment_id="env-net-sniff",
        os_family="linux",
        required_packages=("libpcap-dev", "tcpdump"),
        network_isolation_level="airgapped",
    )

    task = PracticalTaskSpecification(
        task_id="task-p2-sniffer",
        curriculum_node_id="node-f1-p2",
        title="P2: Packet Sniffer Raw Socket",
        difficulty=TaskDifficulty.INTERMEDIATE,
        description="Implementar sniffer IPv4/TCP con AF_PACKET",
        lab_environment=env,
        time_limit_minutes=120,
    )

    assert task.task_id == "task-p2-sniffer"
    assert task.difficulty == TaskDifficulty.INTERMEDIATE
    assert task.lab_environment is not None
    assert task.lab_environment.network_isolation_level == "airgapped"
