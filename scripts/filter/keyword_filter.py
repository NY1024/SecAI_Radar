"""
AI 安全论文关键词筛选器。
通过标题、摘要中的关键词匹配来识别 AI 安全相关论文。
涵盖 ML/LLM/VLM/MLLM 模型安全以及 Agent 安全。
"""

# 核心关键词，匹配标题或摘要中任一即视为 AI 安全相关
SECURITY_KEYWORDS = [
    # === 对抗攻击 (Adversarial Attacks) ===
    "adversarial",
    "adversarial attack",
    "adversarial defense",
    "adversarial robustness",
    "adversarial training",
    "evasion attack",
    # === 后门与投毒 (Backdoor & Poisoning) ===
    "backdoor",
    "backdoor attack",
    "data poisoning",
    "poisoning attack",
    "trojan",
    "trojan attack",
    # === 模型窃取与隐私 (Model Extraction & Privacy) ===
    "model extraction",
    "model stealing",
    "model inversion",
    "membership inference",
    "privacy-preserving",
    "privacy attack",
    "differential privacy",
    "federated security",
    "federated learning privacy",
    # === LLM/VLM/MLLM 安全 (LLM/VLM/MLLM Safety) ===
    "prompt injection",
    "jailbreak",
    "jailbreaking",
    "LLM safety",
    "LLM security",
    "red teaming",
    "red-teaming",
    "AI safety",
    "AI security",
    "machine learning security",
    "ML security",
    "vision language model safety",
    "VLM safety",
    "VLM security",
    "multimodal safety",
    "multimodal security",
    "MLLM safety",
    "MLLM security",
    "multimodal large language model safety",
    # === 可信 AI (Trustworthy AI) ===
    "trustworthy AI",
    "trustworthy machine learning",
    "robustness",
    "certified robustness",
    "verification of neural",
    "formal verification",
    # === 隐私推理与属性推断 (Privacy Inference & Attribute Inference) ===
    "distribution inference",
    "attribute inference",
    "property inference",
    "reconstruction attack",
    "label inference",
    "membership inference",
    "private inference",
    "privacy-aware",
    "privacy-preserving",
    # === 公平性安全 (Fairness) ===
    "fairness attack",
    "fairness manipulation",
    "fairness verification",
    "fairness unlearning",
    "sensitive attribute",
    "sensitive attributes reconstruction",
    "algorithmic recourse",
    # === 机器遗忘与数据删除 (Machine Unlearning) ===
    "machine unlearning",
    "data unlearning",
    "unlearning",
    # === 可解释性安全 (Explainability Security) ===
    "explainable machine learning",
    "explainable AI",
    "interpretable",
    "interpretability",
    # === 联邦学习安全 (Federated Learning Security) ===
    "federated learning",
    "split learning",
    "collaborative learning",
    "private collaborative",
    # === 差分隐私与隐私增强技术 (Differential Privacy & PETs) ===
    "differential privacy",
    "privacy amplification",
    "secure aggregation",
    # === 模型水印与溯源 (Watermark & Provenance) ===
    "watermark",
    "model watermarking",
    "deepfake",
    "deepfake detection",
    # === 图像/文本安全 (Image/Text Security) ===
    "adversarial patch",
    "physical adversarial",
    "evasion",
    # === Agent 安全 (Agent Security) ===
    "agent safety",
    "agent security",
    "LLM agent safety",
    "LLM agent security",
    "agent attack",
    "agent defense",
    "agent red teaming",
    "tool use attack",
    "tool-use attack",
    "tool injection",
    "agent injection",
    "indirect prompt injection",
    "agent poisoning",
    "multi-agent safety",
    "multi-agent security",
    "agentic safety",
    "agentic security",
    "agent manipulation",
    "agent hijacking",
    "function calling attack",
    "function calling security",
    "MCP security",
    "model context protocol security",
    "agent sandbox",
    "agent access control",
    "agent permission",
    "tool calling safety",
]

# 模糊匹配时统一转小写
KEYWORDS_LOWER = [kw.lower() for kw in SECURITY_KEYWORDS]


def is_security_related(title: str, abstract: str = "") -> bool:
    """
    判断论文是否与 AI 安全相关。
    在标题或摘要中匹配任一关键词即返回 True。

    Args:
        title: 论文标题
        abstract: 论文摘要（可选）

    Returns:
        bool: 是否为 AI 安全相关论文
    """
    text = f"{title} {abstract}".lower()
    return any(kw in text for kw in KEYWORDS_LOWER)


def get_matched_keywords(title: str, abstract: str = "") -> list:
    """
    返回匹配到的关键词列表，用于展示。
    """
    text = f"{title} {abstract}".lower()
    matched = []
    for kw in KEYWORDS_LOWER:
        if kw in text:
            # 返回原始大小写版本
            idx = KEYWORDS_LOWER.index(kw)
            matched.append(SECURITY_KEYWORDS[idx])
    return matched
