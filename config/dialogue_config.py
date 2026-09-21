DIALOGUE_CONFIG = {
    "max_dialogue_turns": 8,
    "max_reformulations": 3,
    "max_confusion": 2,
    "max_examples": 2,
    "max_response_words": 150,
    "max_question_words": 40,
    "history_window": 3,
    "min_evidence_for_answer": 1,
    "off_topic_redirect": True,
    
    # CORREGIDO: Sin pool global
    "allow_global_pool_fallback": False,
    
    # CORREGIDO: Solo bridges autorizados
    "allow_bridge_fallback": True,
    "bridge_config_path": "config/bridges.allowlist.json",
}
