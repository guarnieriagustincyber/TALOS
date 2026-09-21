"""Curriculum and Epistemic Roadmap Endpoints (Hito 10)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from study_engine.roadmap.contracts import CurricularRoadmap
from study_engine.web.dependencies import (
    AppContainer,
    generate_mermaid_roadmap,
    get_container,
)
from study_engine.web.schemas import (
    AuthorizedSourceDto,
    CurriculumGraphResponse,
    NodeDetailResponse,
    PracticalTaskSummaryDto,
    RoadmapEdgeDto,
    RoadmapNodeDto,
    RoadmapResponse,
)

router = APIRouter(prefix="/api/curriculum", tags=["Curriculum"])


@router.get("/roadmap", response_model=RoadmapResponse)
def get_roadmap(
    notebook_id: Optional[str] = None,
    container: AppContainer = Depends(get_container),
) -> RoadmapResponse:
    """Retrieve full curricular roadmap graph with pre-rendered Mermaid.js markup.
    
    If notebook_id is provided and matches a registered notebook catalog,
    returns the notebook-specific KC topology, student BKT progression, and DAG.
    Otherwise falls back to the global pipeline roadmap.
    """
    # 1. Check if notebook_id matches a notebook in pedagogical catalog
    catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
    if notebook_id and notebook_id in catalog:
        nb_data = catalog[notebook_id]
        roadmap_id = nb_data.get("curriculum_id", f"roadmap_{notebook_id}")
        title = nb_data.get("name", notebook_id)
        kcs = nb_data.get("kcs", [])

        # Fetch BKT states for student
        nodes_dto: List[RoadmapNodeDto] = []
        edges_dto: List[RoadmapEdgeDto] = []
        mermaid_lines: List[str] = ["graph TD"]

        for kc in kcs:
            kc_id = kc.get("kc_id", "")
            kc_title = kc.get("title", kc_id)
            prereqs = kc.get("prerequisites", [])
            bkt_state = container.bkt_tracker.get_state(kc_id)
            p_L = bkt_state.p_L if bkt_state else 0.0

            if p_L >= 0.85:
                status_str = "MASTERED"
                css_class = "assessed_proficient"
            elif p_L >= 0.40:
                status_str = "IN_PROGRESS"
                css_class = "in_progress"
            else:
                # Check prerequisites met
                prereqs_met = True
                for p in prereqs:
                    p_state = container.bkt_tracker.get_state(p)
                    if not p_state or p_state.p_L < 0.60:
                        prereqs_met = False
                        break
                status_str = "AVAILABLE" if prereqs_met else "LOCKED"
                css_class = "available" if prereqs_met else "locked"

            subtopics = kc.get("subtopics", [])
            description = kc.get("objetivo") or kc.get("description") or f"Contenido curricular correspondiente a {kc_title}."
            unit_val = kc.get("unit") or kc.get("tramo")

            nodes_dto.append(
                RoadmapNodeDto(
                    node_id=kc_id,
                    title=kc_title,
                    status=status_str,
                    prerequisites=prereqs,
                    is_root=(len(prereqs) == 0),
                    node_type="TOPIC",
                    subtopics=subtopics,
                    description=description,
                    unit=unit_val,
                )
            )

            clean_title = kc_title.replace('"', "'")
            mermaid_lines.append(f'  {kc_id}["{clean_title}"]:::{css_class}')

            for p in prereqs:
                edges_dto.append(
                    RoadmapEdgeDto(
                        from_node=p,
                        to_node=kc_id,
                        dependency_type="HARD",
                    )
                )
                mermaid_lines.append(f"  {p} --> {kc_id}")

        mermaid_lines.append("  classDef assessed_proficient fill:#2563eb,stroke:#1d4ed8,color:#ffffff,stroke-width:2px;")
        mermaid_lines.append("  classDef available fill:#059669,stroke:#047857,color:#ffffff,stroke-width:2px;")
        mermaid_lines.append("  classDef in_progress fill:#d97706,stroke:#b45309,color:#ffffff,stroke-width:2px;")
        mermaid_lines.append("  classDef locked fill:#4b5563,stroke:#374151,color:#9ca3af,stroke-width:1px;")
        mermaid_source = "\n".join(mermaid_lines)

        return RoadmapResponse(
            roadmap_id=roadmap_id,
            title=title,
            nodes=nodes_dto,
            edges=edges_dto,
            mermaid_source=mermaid_source,
        )

    # 2. Fallback to global authoritative roadmap
    roadmap: CurricularRoadmap = container.get_roadmap()
    student_state = container.get_current_student_state()

    # Map prerequisites per node
    prereqs_map: dict[str, List[str]] = {nid: [] for nid in roadmap.nodes}
    edges_dto: List[RoadmapEdgeDto] = []

    for dep in roadmap.dependencies:
        prereqs_map.setdefault(dep.target_node_id, []).append(dep.source_node_id)
        edges_dto.append(
            RoadmapEdgeDto(
                from_node=dep.source_node_id,
                to_node=dep.target_node_id,
                dependency_type=dep.dependency_type.value,
            )
        )

    nodes_dto: List[RoadmapNodeDto] = []
    for nid, node in roadmap.nodes.items():
        node_state = student_state.get_node_state(nid)
        node_status = (
            node_state.status.value
            if node_state and hasattr(node_state.status, "value")
            else (str(node_state.status) if node_state else "LOCKED")
        )
        prereqs = prereqs_map.get(nid, [])
        nodes_dto.append(
            RoadmapNodeDto(
                node_id=nid,
                title=node.title,
                status=node_status,
                prerequisites=prereqs,
                is_root=(len(prereqs) == 0),
                node_type=node.node_type.value if hasattr(node.node_type, "value") else str(node.node_type),
            )
        )

    mermaid_source = generate_mermaid_roadmap(roadmap, student_state)

    return RoadmapResponse(
        roadmap_id=roadmap.roadmap_id,
        title=roadmap.title,
        nodes=nodes_dto,
        edges=edges_dto,
        mermaid_source=mermaid_source,
    )


@router.get("/nodes/{node_id}", response_model=NodeDetailResponse)
def get_node_detail(
    node_id: str,
    notebook_id: Optional[str] = None,
    container: AppContainer = Depends(get_container),
) -> NodeDetailResponse:
    """Retrieve in-depth curricular and epistemic specification for a specific node."""
    catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
    
    # Check in catalog if node_id belongs to a notebook KC
    catalog_kc: Optional[dict] = None
    for nb_id, nb_data in catalog.items():
        if notebook_id and nb_id != notebook_id:
            continue
        for k in nb_data.get("kcs", []):
            if k.get("kc_id") == node_id:
                catalog_kc = k
                break
        if catalog_kc:
            break

    if catalog_kc:
        kc_title = catalog_kc.get("title", node_id)
        prereqs = catalog_kc.get("prerequisites", [])
        bkt_state = container.bkt_tracker.get_state(node_id)
        p_L = bkt_state.p_L if bkt_state else 0.0
        if p_L >= 0.85:
            node_status = "MASTERED"
        elif p_L >= 0.40:
            node_status = "IN_PROGRESS"
        else:
            prereqs_met = all(
                (container.bkt_tracker.get_state(p) and container.bkt_tracker.get_state(p).p_L >= 0.60)
                for p in prereqs
            )
            node_status = "AVAILABLE" if prereqs_met else "LOCKED"

        sources = [
            AuthorizedSourceDto(
                document_id=f"doc_{node_id.lower().replace('-', '_')}.pdf",
                page_start=1,
                page_end=10,
            )
        ]
        return NodeDetailResponse(
            node_id=node_id,
            title=kc_title,
            description=f"Objetivo curricular: {kc_title}. Estado contextual: {catalog_kc.get('contextual_status', 'Programa Oficial')}.",
            status=node_status,
            prerequisites=prereqs,
            authorized_sources=sources,
            practical_task=None,
        )

    roadmap: CurricularRoadmap = container.get_roadmap()
    if node_id not in roadmap.nodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curricular node '{node_id}' not found in roadmap '{roadmap.roadmap_id}'",
        )

    node = roadmap.nodes[node_id]
    student_state = container.get_current_student_state()
    node_state = student_state.get_node_state(node_id)
    node_status = (
        node_state.status.value
        if node_state and hasattr(node_state.status, "value")
        else (str(node_state.status) if node_state else "LOCKED")
    )

    # Collect incoming prerequisites
    prereqs = [
        dep.source_node_id
        for dep in roadmap.dependencies
        if dep.target_node_id == node_id
    ]

    # Look up authorized sources if available
    sources: List[AuthorizedSourceDto] = []
    try:
        scoped = container.curriculum_registry.get_scoped_sources_for_node(node_id)
        for doc in scoped:
            sources.append(
                AuthorizedSourceDto(
                    document_id=doc.document_id,
                    page_start=doc.page_start,
                    page_end=doc.page_end,
                )
            )
    except Exception:
        # Fallback to general authorized source for this node
        sources.append(
            AuthorizedSourceDto(
                document_id=f"doc_{node_id.lower().replace('-', '_')}.pdf",
                page_start=1,
                page_end=10,
            )
        )

    # Look up practical task if configured
    practical_task: Optional[PracticalTaskSummaryDto] = None
    task_mapping = container.controller.tutor_policy.config.node_to_task_mapping
    if node_id in task_mapping:
        task_id = task_mapping[node_id].replace(".json", "")
        practical_task = PracticalTaskSummaryDto(
            task_id=task_id,
            description=f"Desafío práctico de programación para maestría en {node.title}.",
            rubric_id=f"RUBRIC-{node_id}",
        )

    return NodeDetailResponse(
        node_id=node.node_id,
        title=node.title,
        description=node.description or f"Contenido curricular correspondiente a {node.title}.",
        status=node_status,
        prerequisites=prereqs,
        authorized_sources=sources,
        practical_task=practical_task,
    )


@router.get("/graph", response_model=CurriculumGraphResponse)
def get_curriculum_graph(
    container: AppContainer = Depends(get_container),
) -> CurriculumGraphResponse:
    """Retrieve curriculum graph topology, Bezier curves, and telemetry for the UI.

    [DESACTIVADO - FIX 1.4 / 2.2]: El grafo visual estático se desactiva para evitar
    inconsistencias 404 con /nodes/{id}. La topología curricular autoritativa se
    debe consultar a través de /api/curriculum/roadmap.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Grafo curricular visual no disponible. Usar /api/curriculum/roadmap.",
    )

