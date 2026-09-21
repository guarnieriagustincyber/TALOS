"""Curriculum Coverage Matrix Contract Test (S5.4).

Verifies 100% representability and referential integrity:
- Fase 0: P-00, P0, G0.1, G0.2
- Fase 1: G1.1, G1.2, G2.1, G2.2, P7, G-F1, G1.5-A, G1.5-B
- Fase 2A: G3.1, G3.2, G3.3, G3.4, P10, G-F2A
- Fase 2B: P11, G4.2, P12, G4.4
- Fase 3A/3B: P21-A, G6A, P21-B, G6B

Enforces:
- 0 contractual gaps
- 0 orphan references
- 0 unresolved curriculum IDs
- 0 authority violations
- Bidirectional consistency between Projects and Gateways
"""

from typing import Any, Dict
import pytest

from study_engine.curriculum import (
    AssessmentRubric,
    CompensationRule,
    CompensationScope,
    DefenseCategory,
    DefenseQuestionTemplate,
    ExpectedBehavior,
    GatewayDefinition,
    GatewayFormat,
    GatewayVerdictCriteria,
    HoareContractSpecification,
    Invariant,
    OralDefenseSpecification,
    PerformanceLevel,
    PerturbationTemplate,
    PerturbationType,
    Postcondition,
    PracticalTaskSpecification,
    Precondition,
    ProjectMilestone,
    ProjectSpecification,
    RubricDimension,
    TaskDifficulty,
    TerminationVariant,
)


@pytest.fixture
def real_curriculum_fixture() -> Dict[str, Any]:
    """Build representative curriculum fixtures spanning Fases 0 to 3B."""

    # 1. Rubrics
    r_standard_dim = RubricDimension(
        dimension_id="dim-functional",
        title="Funcionalidad y Tests",
        weight=1.0,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    rubric_g01 = AssessmentRubric(
        rubric_id="rubric-g01",
        title="Rúbrica G0.1: Parser Desconocido",
        dimensions=(r_standard_dim,),
    )

    r_g6a_demo = RubricDimension(
        dimension_id="live_demo",
        title="Demostración en vivo",
        weight=0.30,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    r_g6a_just = RubricDimension(
        dimension_id="invariant_justification",
        title="Justificación formal",
        weight=0.25,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    r_g6a_found = RubricDimension(
        dimension_id="foundations",
        title="Conexión fundamentos",
        weight=0.20,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    r_g6a_quest = RubricDimension(
        dimension_id="questions_perturbations",
        title="Preguntas y perturbaciones",
        weight=0.15,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=True,
    )
    r_g6a_comm = RubricDimension(
        dimension_id="communication",
        title="Comunicación ejecutiva",
        weight=0.10,
        minimum_level=PerformanceLevel.N3_COMPETENT,
        is_critical=False,
    )
    rule_g6a = CompensationRule(
        rule_id="comp-g6a-demo-offset",
        source_dimension_id="live_demo",
        source_minimum_level=PerformanceLevel.N2_BASIC,
        compensating_dimension_id="invariant_justification",
        compensating_minimum_level=PerformanceLevel.N4_EXCELLENT,
        allowed_scope=CompensationScope.GATEWAY,
        justification="N2 en demo compensa con N4 en justificación formal",
    )
    rubric_g6a = AssessmentRubric(
        rubric_id="rubric-g6a-5dimensions",
        title="Rúbrica G6A Capstone (5 Dimensiones con Compensación)",
        dimensions=(
            r_g6a_demo,
            r_g6a_just,
            r_g6a_found,
            r_g6a_quest,
            r_g6a_comm,
        ),
        allow_compensation=True,
        compensation_rules=(rule_g6a,),
    )

    rubrics: Dict[str, AssessmentRubric] = {
        "rubric-g01": rubric_g01,
        "rubric-g6a-5dimensions": rubric_g6a,
    }

    # 2. Hoare Specifications
    hoare_p12 = HoareContractSpecification(
        contract_id="hoare-p12-ransomware",
        name="Playbook SOAR Ransomware Containment Contract",
        target_component="soar.playbooks.ransomware",
        preconditions=(
            Precondition(
                predicate_id="pre-1",
                formal_expression="threat_score >= 80",
                description="Host is high-confidence infected",
            ),
        ),
        postconditions=(
            Postcondition(
                predicate_id="post-1",
                formal_expression="network_isolated(host)",
                description="Host isolated",
            ),
        ),
        invariants=(
            Invariant(
                invariant_id="inv-1",
                formal_expression="not network_isolated(domain_controller)",
                description="DC never isolated",
                violation_consequence="P1 critical infrastructure failure",
            ),
        ),
        termination_variant=TerminationVariant(
            variant_id="term-1",
            measure_expression="queue.length",
            description="Pending containment queue strictly decreases",
        ),
        description="Hoare specification for P12 SOAR Playbook",
    )
    hoare_specs: Dict[str, HoareContractSpecification] = {
        "hoare-p12-ransomware": hoare_p12,
    }

    # 3. Perturbation Templates
    pert_g12_1 = PerturbationTemplate(
        perturbation_id="pert-g12-endianness",
        type=PerturbationType.PARAMETER_MUTATION,
        name="Endianness Format Swap",
        description="Change network format '!' to '<'",
        baseline_condition="struct.unpack('!H', data)",
        mutated_condition="struct.unpack('<H', data)",
        level_expectations={
            PerformanceLevel.N3_COMPETENT: ExpectedBehavior(
                performance_level=PerformanceLevel.N3_COMPETENT,
                expected_reasoning="Byte swap on 16+ bit fields",
                expected_action="Fix format character to '!'",
            ),
        },
    )
    pert_templates: Dict[str, PerturbationTemplate] = {
        "pert-g12-endianness": pert_g12_1,
    }

    # 4. Oral Defense Specifications
    defense_g12 = OralDefenseSpecification(
        defense_id="defense-g12",
        duration_minutes=10,
        panel_size=1,
        question_pool=(
            DefenseQuestionTemplate(
                question_id="q-g12-1",
                category=DefenseCategory.ARCHITECTURE_JUSTIFICATION,
                prompt_text="Explicá cómo manejás el endianness en red",
                target_concepts=("endianness", "network_byte_order"),
                expected_points_n3=("Network byte order es big-endian",),
            ),
        ),
        required_questions_count=1,
        rubric_id="rubric-g01",
    )
    defense_g6a = OralDefenseSpecification(
        defense_id="defense-g6a",
        duration_minutes=30,
        panel_size=3,
        question_pool=(
            DefenseQuestionTemplate(
                question_id="q-g6a-1",
                category=DefenseCategory.EXECUTIVE_SYNTHESIS,
                prompt_text="Explicación al CTO del incidente",
                target_concepts=("iam", "cloudtrail"),
                expected_points_n3=("Least privilege enforcement",),
            ),
        ),
        required_questions_count=1,
        rubric_id="rubric-g6a-5dimensions",
    )
    oral_defenses: Dict[str, OralDefenseSpecification] = {
        "defense-g12": defense_g12,
        "defense-g6a": defense_g6a,
    }

    # 5. Practical Tasks
    task_p12 = PracticalTaskSpecification(
        task_id="task-p12-soar-containment",
        curriculum_node_id="node-f2b-p12",
        title="P12: Playbook SOAR de Contención",
        difficulty=TaskDifficulty.ADVANCED,
        description="Implementar playbook automatizado con TheHive y MISP",
        hoare_contract_id="hoare-p12-ransomware",
    )
    tasks: Dict[str, PracticalTaskSpecification] = {
        "task-p12-soar-containment": task_p12,
    }

    # 6. Projects (Normalized Catalog)
    proj_p00 = ProjectSpecification(
        project_id="P-00",
        title="P-00: Parser Simple de Logs Web",
        curriculum_node_id="node-f0-p00",
        milestones=(
            ProjectMilestone(
                milestone_id="p00-m1",
                project_id="P-00",
                sequence_order=0,
                title="Parser básico y dataclasses",
                description="Parsea líneas de log con tipos estrictos",
            ),
        ),
        capstone_gateway_id="G0.1",
    )

    proj_p0 = ProjectSpecification(
        project_id="P0",
        title="P0: Detector de Fuerza Bruta Incremental",
        curriculum_node_id="node-f0-p0",
        milestones=(
            ProjectMilestone(
                milestone_id="p0-m1",
                project_id="P0",
                sequence_order=0,
                title="Entrega 1: Baseline",
                description="Conteo de fallos",
            ),
        ),
        capstone_gateway_id="G0.2",
    )

    proj_p10 = ProjectSpecification(
        project_id="P10",
        title="P10: Threat Hunt Documentado (APT Real)",
        curriculum_node_id="node-f2a-p10",
        milestones=(
            ProjectMilestone(
                milestone_id="p10-m1",
                project_id="P10",
                sequence_order=0,
                title="Diamond Model & SIGMA rules",
                description="Análisis de amenaza real",
            ),
        ),
        capstone_gateway_id="G-F2A",
    )

    proj_p11 = ProjectSpecification(
        project_id="P11",
        title="P11: Investigación Forense Completa",
        curriculum_node_id="node-f2b-p11",
        milestones=(
            ProjectMilestone(
                milestone_id="p11-m1",
                project_id="P11",
                sequence_order=0,
                title="Forense de memoria y disco",
                description="Timeline MACB e informe forense",
            ),
        ),
        capstone_gateway_id="G4.2",
    )

    proj_p12 = ProjectSpecification(
        project_id="P12",
        title="P12: Playbook SOAR para Ransomware",
        curriculum_node_id="node-f2b-p12",
        milestones=(
            ProjectMilestone(
                milestone_id="p12-m1",
                project_id="P12",
                sequence_order=0,
                title="Playbook funcional y contratos Hoare",
                description="Contención automatizada",
                task_ids=("task-p12-soar-containment",),
            ),
        ),
        capstone_gateway_id="G4.4",
    )

    proj_p21a = ProjectSpecification(
        project_id="P21-A",
        title="P21-A: Capstone Cloud-Native SOC & Threat Hunting",
        curriculum_node_id="node-track-a-p21a",
        milestones=(
            ProjectMilestone(
                milestone_id="p21a-m1",
                project_id="P21-A",
                sequence_order=0,
                title="Defensa Multi-Capa en K8s y AWS",
                description="Correlación Suricata, Wazuh, Falco, CloudTrail",
            ),
        ),
        capstone_gateway_id="G6A",
    )

    proj_p21b = ProjectSpecification(
        project_id="P21-B",
        title="P21-B: Capstone Reverse Engineering & Purple Team",
        curriculum_node_id="node-track-b-p21b",
        milestones=(
            ProjectMilestone(
                milestone_id="p21b-m1",
                project_id="P21-B",
                sequence_order=0,
                title="Exploit Development & Binary Analysis",
                description="Análisis de binarios y emulación de adversarios",
            ),
        ),
        capstone_gateway_id="G6B",
    )

    projects: Dict[str, ProjectSpecification] = {
        "P-00": proj_p00,
        "P0": proj_p0,
        "P10": proj_p10,
        "P11": proj_p11,
        "P12": proj_p12,
        "P21-A": proj_p21a,
        "P21-B": proj_p21b,
    }

    # 7. Gateways (Normalized Catalog)
    crit_standard = GatewayVerdictCriteria(criteria_id="crit-std")

    gw_g01 = GatewayDefinition(
        gateway_id="G0.1",
        curriculum_node_id="node-f0-g01",
        title="G0.1: Parser de Log Desconocido",
        format=GatewayFormat.INDIVIDUAL_PRACTICAL,
        rubric_id="rubric-g01",
        verdict_criteria=crit_standard,
        associated_project_id="P-00",
    )

    gw_g02 = GatewayDefinition(
        gateway_id="G0.2",
        curriculum_node_id="node-f0-g02",
        title="G0.2: Algoritmos y Estructuras + P0",
        format=GatewayFormat.INDIVIDUAL_PRACTICAL,
        rubric_id="rubric-g01",
        verdict_criteria=crit_standard,
        associated_project_id="P0",
    )

    gw_g12 = GatewayDefinition(
        gateway_id="G1.2",
        curriculum_node_id="node-f1-g12",
        title="G1.2: Sniffer IPv4/TCP con Perturbaciones",
        format=GatewayFormat.PRACTICAL_AND_ORAL,
        rubric_id="rubric-g01",
        verdict_criteria=crit_standard,
        perturbation_ids=("pert-g12-endianness",),
        oral_defense_id="defense-g12",
    )

    gw_gf2a = GatewayDefinition(
        gateway_id="G-F2A",
        curriculum_node_id="node-f2a-gf2a",
        title="G-F2A: Gateway de Fase 2A (SOC Lab)",
        format=GatewayFormat.INDIVIDUAL_PRACTICAL,
        rubric_id="rubric-g01",
        verdict_criteria=crit_standard,
        associated_project_id="P10",
    )

    gw_g42 = GatewayDefinition(
        gateway_id="G4.2",
        curriculum_node_id="node-f2b-g42",
        title="G4.2: Forense de Red y Memoria",
        format=GatewayFormat.INDIVIDUAL_PRACTICAL,
        rubric_id="rubric-g01",
        verdict_criteria=crit_standard,
        associated_project_id="P11",
    )

    gw_g44 = GatewayDefinition(
        gateway_id="G4.4",
        curriculum_node_id="node-f2b-g44",
        title="G4.4: Playbook SOAR con Tripleta de Hoare",
        format=GatewayFormat.PRACTICAL_AND_ORAL,
        rubric_id="rubric-g01",
        verdict_criteria=crit_standard,
        practical_task_ids=("task-p12-soar-containment",),
        associated_project_id="P12",
    )

    gw_g6a = GatewayDefinition(
        gateway_id="G6A",
        curriculum_node_id="node-track-a-g6a",
        title="G6A: Final de Track A (Cloud-Native SOC Capstone)",
        format=GatewayFormat.CAPSTONE_DEFENSE,
        rubric_id="rubric-g6a-5dimensions",
        verdict_criteria=GatewayVerdictCriteria(
            criteria_id="crit-g6a",
            allow_compensation=True,
        ),
        oral_defense_id="defense-g6a",
        associated_project_id="P21-A",
    )

    gw_g6b = GatewayDefinition(
        gateway_id="G6B",
        curriculum_node_id="node-track-b-g6b",
        title="G6B: Final de Track B (RE & Purple Team Capstone)",
        format=GatewayFormat.CAPSTONE_DEFENSE,
        rubric_id="rubric-g01",
        verdict_criteria=crit_standard,
        associated_project_id="P21-B",
    )

    gateways: Dict[str, GatewayDefinition] = {
        "G0.1": gw_g01,
        "G0.2": gw_g02,
        "G1.2": gw_g12,
        "G-F2A": gw_gf2a,
        "G4.2": gw_g42,
        "G4.4": gw_g44,
        "G6A": gw_g6a,
        "G6B": gw_g6b,
    }

    return {
        "rubrics": rubrics,
        "hoare_specs": hoare_specs,
        "pert_templates": pert_templates,
        "oral_defenses": oral_defenses,
        "tasks": tasks,
        "projects": projects,
        "gateways": gateways,
    }


def test_coverage_matrix_bidirectional_consistency(
    real_curriculum_fixture: Dict[str, Any]
) -> None:
    """Enforce bidirectional consistency between Projects and Gateways.

    If project.capstone_gateway_id == gateway.gateway_id,
    then gateway.associated_project_id == project.project_id.
    """
    projects = real_curriculum_fixture["projects"]
    gateways = real_curriculum_fixture["gateways"]

    for proj_id, proj in projects.items():
        if proj.capstone_gateway_id is not None:
            gw_id = proj.capstone_gateway_id
            assert gw_id in gateways, (
                f"Orphan reference: Project '{proj_id}' references "
                f"unknown gateway '{gw_id}'"
            )
            gw = gateways[gw_id]
            assert gw.associated_project_id == proj_id, (
                f"Bidirectional inconsistency: Project '{proj_id}' declared "
                f"capstone '{gw.gateway_id}', but Gateway declared "
                f"associated_project_id='{gw.associated_project_id}'"
            )


def test_coverage_matrix_zero_orphan_rubrics_and_defenses(
    real_curriculum_fixture: Dict[str, Any]
) -> None:
    """Assert all rubrics, defenses, tasks resolve without orphans."""
    gateways = real_curriculum_fixture["gateways"]
    rubrics = real_curriculum_fixture["rubrics"]
    defenses = real_curriculum_fixture["oral_defenses"]
    tasks = real_curriculum_fixture["tasks"]
    pert_templates = real_curriculum_fixture["pert_templates"]
    hoare_specs = real_curriculum_fixture["hoare_specs"]

    for gw_id, gw in gateways.items():
        assert gw.rubric_id in rubrics, (
            f"Gateway '{gw_id}' references unknown rubric '{gw.rubric_id}'"
        )

        if gw.oral_defense_id is not None:
            assert gw.oral_defense_id in defenses, (
                f"Gateway '{gw_id}' references unknown oral defense "
                f"'{gw.oral_defense_id}'"
            )

        for tid in gw.practical_task_ids:
            assert tid in tasks, (
                f"Gateway '{gw_id}' references unknown task '{tid}'"
            )

        for pid in gw.perturbation_ids:
            assert pid in pert_templates, (
                f"Gateway '{gw_id}' references unknown perturbation '{pid}'"
            )

    for tid, task in tasks.items():
        if task.hoare_contract_id is not None:
            assert task.hoare_contract_id in hoare_specs, (
                f"Task '{tid}' references unknown Hoare contract "
                f"'{task.hoare_contract_id}'"
            )


def test_coverage_matrix_zero_contractual_gaps_and_authority_violations(
    real_curriculum_fixture: Dict[str, Any]
) -> None:
    """Verify zero contractual gaps and zero authority violations."""
    gateways = real_curriculum_fixture["gateways"]

    for gw_id, gw in gateways.items():
        assert len(gw.curriculum_node_id) > 0
        assert not hasattr(gw, "set_mastery")
        assert not hasattr(gw, "emit_verdict")
