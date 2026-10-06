import json

with open('experiments/v1_5_ingestion/probe1/colab_test_results/results/masking_key_unblind.json') as f:
    masking_key = json.load(f)

with open('experiments/v1_5_ingestion/probe1/PROBE1_TEST_ROUTER_RESULTS.jsonl') as f:
    router_results = {json.loads(l)['page_id']: json.loads(l) for l in f if l.strip()}

# Detailed adjudication database for all 19 TEST pages
adjudication_data = [
    {
        'page_id': 'joyanes_ch02_p076',
        'physical_page_number': 76,
        'logical_page_number': 46,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'HEADING': 3, 'ORDER': 3},
            'docling': {'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': False,
        'reference_basis': 'EXPOSITORY_PROSE_EQUIVALENCE',
        'rationale': 'Clean expository prose with section 2.1 heading and bullet list. PyMuPDF extracts text identically without loss. Docling provides no material structural benefit.'
    },
    {
        'page_id': 'joyanes_ch02_p077',
        'physical_page_number': 77,
        'logical_page_number': 47,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['DIAGRAM', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'DIAGRAM': 1, 'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'DIAGRAM': 2, 'HEADING': 3, 'ORDER': 3},
            'docling': {'DIAGRAM': 2, 'HEADING': 3, 'ORDER': 2}
        },
        'docling_beneficial': False,
        'reference_basis': 'MIXED_CONCEPT_SCHEMA_AND_FORMULA',
        'rationale': 'Fig 2.1 conceptual boxes. Docling isolates image but drops the formula at bottom (<!-- formula-not-decoded -->). PyMuPDF preserves formula text and readable box labels. Docling provides no net benefit.'
    },
    {
        'page_id': 'joyanes_ch02_p078',
        'physical_page_number': 78,
        'logical_page_number': 48,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['TABLE', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'TABLE': 0, 'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'TABLE': 0, 'HEADING': 3, 'ORDER': 3},
            'docling': {'TABLE': 3, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': True,
        'reference_basis': 'BORDERLESS_TABLE_RESCUE',
        'rationale': '4-column borderless depreciation table. PyMuPDF linearizes columns into single vertical stream (Score 0). Docling reconstructs a perfect Markdown table (Score 3). Critical structural gain (Condition A).'
    },
    {
        'page_id': 'joyanes_ch02_p081',
        'physical_page_number': 81,
        'logical_page_number': 51,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['CODE', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'CODE': 3, 'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'CODE': 3, 'HEADING': 3, 'ORDER': 3},
            'docling': {'CODE': 1, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': False,
        'reference_basis': 'DOCLING_CODE_COLLAPSE_REGRESSION',
        'rationale': 'Example 2.2 pseudocode algorithm. PyMuPDF preserves multi-line indented structure. Docling collapses code block into a single contiguous line (Score 1). Docling is strictly inferior.'
    },
    {
        'page_id': 'joyanes_ch02_p085',
        'physical_page_number': 85,
        'logical_page_number': 55,
        'typology': 'MIXED_DIAGRAM_AND_PROSE',
        'applicable_dimensions': ['DIAGRAM', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'DIAGRAM': 1, 'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'DIAGRAM': 1, 'HEADING': 3, 'ORDER': 3},
            'docling': {'DIAGRAM': 3, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': True,
        'reference_basis': 'DIAGRAM_ISOLATION_RESCUE',
        'rationale': 'Fig 2.7 local/global variables diagram. PyMuPDF dumps 8 box labels into prose. Docling cleanly isolates diagram as image (Score 3). Significant structural gain (Condition A).'
    },
    {
        'page_id': 'joyanes_ch02_p088',
        'physical_page_number': 88,
        'logical_page_number': 58,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'HEADING': 3, 'ORDER': 3},
            'docling': {'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': False,
        'reference_basis': 'EXPOSITORY_PROSE_EQUIVALENCE',
        'rationale': 'Expository prose on abstraction and encapsulation. Clean headings and paragraph order in both extractors. Tie-break rule applies.'
    },
    {
        'page_id': 'joyanes_ch02_p090',
        'physical_page_number': 90,
        'logical_page_number': 60,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'HEADING': 3, 'ORDER': 3},
            'docling': {'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': False,
        'reference_basis': 'EXPOSITORY_PROSE_EQUIVALENCE',
        'rationale': 'Bulleted taxonomies of real-world objects. Clean itemization in PyMuPDF. Tie-break rule applies.'
    },
    {
        'page_id': 'joyanes_ch02_p092',
        'physical_page_number': 92,
        'logical_page_number': 62,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['DIAGRAM', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'DIAGRAM': 1, 'HEADING': 3, 'ORDER': 2},
            'pymupdf': {'DIAGRAM': 1, 'HEADING': 3, 'ORDER': 2},
            'docling': {'DIAGRAM': 3, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': True,
        'reference_basis': 'UML_DIAGRAM_ISOLATION_RESCUE',
        'rationale': 'Fig 2.11 and 2.12 UML class diagrams. PyMuPDF scrambles class compartments, attributes, and methods into a linear mess. Docling isolates both diagrams as images (Score 3). Condition A satisfied.'
    },
    {
        'page_id': 'joyanes_ch02_p093',
        'physical_page_number': 93,
        'logical_page_number': 63,
        'typology': 'MIXED_DIAGRAM_AND_PROSE',
        'applicable_dimensions': ['DIAGRAM', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'DIAGRAM': 1, 'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'DIAGRAM': 1, 'HEADING': 3, 'ORDER': 3},
            'docling': {'DIAGRAM': 3, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': True,
        'reference_basis': 'UML_INHERITANCE_DIAGRAM_ISOLATION',
        'rationale': 'Fig 2.13 UML class inheritance hierarchy. PyMuPDF leaks diagram text at the bottom. Docling isolates it cleanly as an image block (Score 3). Condition A satisfied.'
    },
    {
        'page_id': 'joyanes_ch02_p094',
        'physical_page_number': 94,
        'logical_page_number': 64,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'HEADING': 3, 'ORDER': 3},
            'docling': {'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': False,
        'reference_basis': 'EXPOSITORY_PROSE_EQUIVALENCE',
        'rationale': 'Expository prose on algorithm definitions with small 3-box pipeline. The text is fully readable in PyMuPDF, while Docling replaces with placeholder. Expository prose equivalence applies.'
    },
    {
        'page_id': 'joyanes_ch02_p098',
        'physical_page_number': 98,
        'logical_page_number': 68,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'HEADING': 3, 'ORDER': 3},
            'docling': {'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': False,
        'reference_basis': 'EXPOSITORY_PROSE_EQUIVALENCE',
        'rationale': 'Section 2.6 narrative prose on writing algorithms. Both extractors preserve headings and paragraphs. Tie-break rule applies.'
    },
    {
        'page_id': 'joyanes_ch02_p099',
        'physical_page_number': 99,
        'logical_page_number': 69,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['CODE', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'CODE': 3, 'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'CODE': 3, 'HEADING': 3, 'ORDER': 3},
            'docling': {'CODE': 1, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': False,
        'reference_basis': 'DOCLING_CODE_COLLAPSE_REGRESSION',
        'rationale': '6-step structured algorithm with nested indentation. PyMuPDF preserves clean indentations and line breaks. Docling collapses the algorithm into a single line inside triple backticks. Docling is strictly inferior.'
    },
    {
        'page_id': 'joyanes_ch02_p104',
        'physical_page_number': 104,
        'logical_page_number': 74,
        'typology': 'FLOWCHART_OR_DIAGRAM',
        'applicable_dimensions': ['DIAGRAM', 'CODE', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'DIAGRAM': 0, 'CODE': 3, 'HEADING': 2, 'ORDER': 1},
            'pymupdf': {'DIAGRAM': 0, 'CODE': 3, 'HEADING': 2, 'ORDER': 1},
            'docling': {'DIAGRAM': 3, 'CODE': 2, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': True,
        'reference_basis': 'PARALLEL_FLOWCHART_ISOLATION_RESCUE',
        'rationale': 'Example 2.8 flowchart side-by-side with pseudocode. PyMuPDF interweaves diagram boxes and pseudocode laterally (Score 0). Docling cleanly isolates diagram as image (Score 3). Condition A satisfied.'
    },
    {
        'page_id': 'joyanes_ch02_p107',
        'physical_page_number': 107,
        'logical_page_number': 77,
        'typology': 'FLOWCHART_OR_DIAGRAM',
        'applicable_dimensions': ['DIAGRAM', 'CODE', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'DIAGRAM': 0, 'CODE': 1, 'HEADING': 2, 'ORDER': 1},
            'pymupdf': {'DIAGRAM': 0, 'CODE': 1, 'HEADING': 2, 'ORDER': 1},
            'docling': {'DIAGRAM': 3, 'CODE': 2, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': True,
        'reference_basis': 'PARALLEL_FLOWCHART_ISOLATION_RESCUE',
        'rationale': 'Example 2.10 flowchart variant side-by-side with pseudocode. PyMuPDF interleaves both columns causing total structural destruction. Docling isolates flowchart as image. Condition A satisfied.'
    },
    {
        'page_id': 'joyanes_ch02_p108',
        'physical_page_number': 108,
        'logical_page_number': 78,
        'typology': 'FLOWCHART_OR_DIAGRAM',
        'applicable_dimensions': ['DIAGRAM', 'CODE', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'DIAGRAM': 0, 'CODE': 3, 'HEADING': 2, 'ORDER': 1},
            'pymupdf': {'DIAGRAM': 0, 'CODE': 3, 'HEADING': 2, 'ORDER': 1},
            'docling': {'DIAGRAM': 3, 'CODE': 2, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': True,
        'reference_basis': 'PARALLEL_FLOWCHART_ISOLATION_RESCUE',
        'rationale': 'Example 2.10 continuation flowchart and pseudocode. PyMuPDF column cross-contamination destroys flow. Docling isolates flowchart as image. Condition A satisfied.'
    },
    {
        'page_id': 'joyanes_ch02_p109',
        'physical_page_number': 109,
        'logical_page_number': 79,
        'typology': 'FLOWCHART_OR_DIAGRAM',
        'applicable_dimensions': ['DIAGRAM', 'CODE', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'DIAGRAM': 0, 'CODE': 3, 'HEADING': 2, 'ORDER': 1},
            'pymupdf': {'DIAGRAM': 0, 'CODE': 3, 'HEADING': 2, 'ORDER': 1},
            'docling': {'DIAGRAM': 3, 'CODE': 2, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': True,
        'reference_basis': 'PARALLEL_FLOWCHART_ISOLATION_RESCUE',
        'rationale': 'Example 2.11 flowchart and pseudocode side-by-side (Fig 2.19). PyMuPDF scrambles two-column text. Docling isolates as image. Condition A satisfied.'
    },
    {
        'page_id': 'joyanes_ch02_p110',
        'physical_page_number': 110,
        'logical_page_number': 80,
        'typology': 'FLOWCHART_OR_DIAGRAM',
        'applicable_dimensions': ['DIAGRAM', 'HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'DIAGRAM': 0, 'HEADING': 2, 'ORDER': 1},
            'pymupdf': {'DIAGRAM': 0, 'HEADING': 2, 'ORDER': 1},
            'docling': {'DIAGRAM': 3, 'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': True,
        'reference_basis': 'NASSI_SCHNEIDERMAN_DIAGRAM_ISOLATION',
        'rationale': 'Section 2.7.3 Nassi-Schneiderman diagrams (Fig 2.20 & 2.21). PyMuPDF completely destroys box structure into scattered lines. Docling preserves diagram as table/image (Score 3). Condition A satisfied.'
    },
    {
        'page_id': 'joyanes_ch02_p111',
        'physical_page_number': 111,
        'logical_page_number': 81,
        'typology': 'EXERCISES_PROBLEMS',
        'applicable_dimensions': ['HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'HEADING': 3, 'ORDER': 3},
            'docling': {'HEADING': 3, 'ORDER': 1}
        },
        'docling_beneficial': False,
        'reference_basis': 'DOCLING_READING_ORDER_TEARING_REGRESSION',
        'rationale': 'Resumen and Ejercicios layout. Docling inserts ## EJERCICIOS in the middle of an incomplete sentence from Resumen, severely corrupting reading order (Score 1). Docling regresses.'
    },
    {
        'page_id': 'joyanes_ch02_p112',
        'physical_page_number': 112,
        'logical_page_number': 82,
        'typology': 'EXPOSITORY_PROSE',
        'applicable_dimensions': ['HEADING', 'ORDER'],
        'scores_by_tool': {
            'pypdf':   {'HEADING': 3, 'ORDER': 3},
            'pymupdf': {'HEADING': 3, 'ORDER': 3},
            'docling': {'HEADING': 3, 'ORDER': 3}
        },
        'docling_beneficial': False,
        'reference_basis': 'EXPOSITORY_PROSE_EQUIVALENCE',
        'rationale': 'Numbered exercise problems list (2.5-2.15). Clean sequential items in PyMuPDF. Tie-break rule applies.'
    }
]

out_lines = []
for entry in adjudication_data:
    pid = entry['page_id']
    m_map = masking_key[pid] # { "TOOL_ALPHA": "pymupdf", ... }
    inv_map = {v: k for k, v in m_map.items()} # { "pymupdf": "TOOL_ALPHA", ... }
    
    # Build blind scores
    blind_scores = {}
    for tool_name, t_scores in entry['scores_by_tool'].items():
        blind_label = inv_map[tool_name]
        blind_scores[blind_label] = t_scores
        
    router_selected = router_results[pid]['decision']['selected_path']
    # Adaptive score
    if router_selected == 'DOCLING':
        entry['scores_by_tool']['adaptive'] = entry['scores_by_tool']['docling']
    else:
        entry['scores_by_tool']['adaptive'] = entry['scores_by_tool']['pymupdf']
        
    line_obj = {
        '$schema': 'https://raw.githubusercontent.com/guarnieriagustincyber/TALOS/main/schemas/probe1_human_adjudication.schema.json',
        'page_id': pid,
        'physical_page_number': entry['physical_page_number'],
        'logical_page_number': entry['logical_page_number'],
        'typology': entry['typology'],
        'applicable_dimensions': entry['applicable_dimensions'],
        'blind_scores': blind_scores,
        'unblind_mapping': m_map,
        'unblinded_scores': entry['scores_by_tool'],
        'docling_beneficial': entry['docling_beneficial'],
        'router_selected': router_selected,
        'outcome_class': 'TP' if entry['docling_beneficial'] and router_selected == 'DOCLING' else (
            'FP' if (not entry['docling_beneficial']) and router_selected == 'DOCLING' else (
                'FN' if entry['docling_beneficial'] and router_selected != 'DOCLING' else 'TN'
            )
        ),
        'reference_basis': entry['reference_basis'],
        'rationale': entry['rationale']
    }
    out_lines.append(json.dumps(line_obj, ensure_ascii=False))

with open('experiments/v1_5_ingestion/probe1/PROBE1_TEST_ADJUDICATION.jsonl', 'w') as f:
    f.write('\n'.join(out_lines) + '\n')

print(f"Generated PROBE1_TEST_ADJUDICATION.jsonl with {len(out_lines)} records.")

