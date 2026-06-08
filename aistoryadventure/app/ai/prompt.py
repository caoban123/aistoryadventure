from __future__ import annotations

from app.domain.models import Message, SessionState, MemoryChunk


def build_start_prompt(
    player_name: str,
    story_style: str | None,
    character_hint: str | None,
    world_hint: str | None,
    adventure_profile: dict | None = None,
    gender: str | None = None,
    personality: str | None = None,
) -> str:
    style_note = f"Phong cách mong muốn: {story_style}." if story_style else ""
    char_note = f"Gợi ý nhân vật: {character_hint}." if character_hint else ""
    world_note = f"Gợi ý thế giới: {world_hint}." if world_hint else ""

    survival_profile = adventure_profile or {}
    survival_note = f"""
SURVIVAL RUN STATE:
- Region: {survival_profile.get("region") or "AI decides"}
- Starting condition: {survival_profile.get("starting_condition") or "AI decides"}
- Objective: {survival_profile.get("objective") or "Survive and move forward"}
- Threat: {survival_profile.get("threat") or "An immediate danger closes in"}
- Loadout: {survival_profile.get("loadout") or "Light supplies"}
- Danger: {survival_profile.get("danger", 3)}/5
- Supplies: {survival_profile.get("supplies", 3)}/5
- Wounds: {survival_profile.get("wounds", 0)}/5
- Time pressure: {survival_profile.get("time_pressure", 3)}/5
""".strip()

    return f"""
Bạn là người kể chuyện chính cho một trò chơi phiêu lưu tương tác.

NGÔN NGỮ: Toàn bộ nội dung người chơi thấy phải bằng tiếng Việt văn học, tự nhiên.

Nhiệm vụ:
Mở ra một thế giới và một khoảnh khắc sống động. Người chơi không đọc câu chuyện — họ đang ở trong đó.

Trả về ĐÚNG định dạng JSON sau. Không thêm markdown, không giải thích ngoài JSON.

{{
  "foundation": "Một đến ba đoạn văn xuôi tiếng Việt thiết lập nền tảng lâu dài: thế giới, nhân vật, xuất phát điểm, những chi tiết quan trọng cần nhớ cho các lượt sau.",
  "story": "Cảnh mở đầu viết hoàn toàn bằng tiếng Việt.",
  "choices": [
    "Lựa chọn ngắn tự nhiên",
    "Lựa chọn ngắn tự nhiên",
    "Lựa chọn ngắn tự nhiên"
  ],
  "survival_update": {{
    "danger": 3,
    "supplies": 3,
    "wounds": 0,
    "time_pressure": 3,
    "last_survival_note": "Short note about the immediate survival pressure."
  }}
}}

Cách viết phần foundation:
Không phải bảng thống kê. Viết như một đoạn giới thiệu trong sổ tay tác giả — thế giới là gì, nhân vật là ai, điều gì đang chờ đợi phía trước. Súc tích, có hồn.

Cách viết phần story:
Bắt đầu giữa chừng một khoảnh khắc — đừng giới thiệu, đừng giải thích. Để không khí, hành động và chi tiết cụ thể tự dẫn người đọc vào.
Tránh các câu mở kiểu "Bạn là...", "Câu chuyện bắt đầu...", hay "Trong một thế giới nơi...".
Tin vào sự mơ hồ có kiểm soát. Người đọc thông minh hơn bạn nghĩ.
Viết ngắn hơn mức bạn cho là cần — sức nặng nằm ở chi tiết, không phải độ dài.

Cách viết phần choices:
Ba lựa chọn ngắn, tự nhiên như lời người ta thực sự nói hoặc làm. Không đánh số.

Thông tin nhân vật:
Tên: {player_name}
Giới tính: {gender or "tùy AI quyết định nếu cần"}
Tính cách: {personality or "tùy AI tạo"}
{style_note}
{char_note}
{world_note}
{survival_note}
""".strip()


def build_novel_world_prompt(world_seed: str | None) -> str:
    return f"""
Bạn là người hỗ trợ xây dựng thế giới cho một ứng dụng viết tiểu thuyết tương tác.

NGÔN NGỮ: Toàn bộ nội dung người dùng thấy phải bằng tiếng Việt tự nhiên.

Nhiệm vụ:
Chưa phải lúc bắt đầu viết câu chuyện. Trước tiên, hãy tạo ra một thế giới đủ sống động để người dùng muốn sống trong đó — rồi đặt câu hỏi giúp họ định hình tiếp.

Trả về ĐÚNG định dạng JSON sau. Không markdown, không giải thích ngoài JSON.

{{
  "world_draft": "Mô tả thế giới bằng tiếng Việt — súc tích nhưng có chiều sâu. Không phải bách khoa toàn thư, mà là cảm giác đầu tiên khi bước vào.",
  "questions": [
    {{
      "id": "q1",
      "question": "Câu hỏi tiếng Việt giúp định hình nhân vật chính, xung đột, giọng điệu hoặc hướng câu chuyện.",
      "suggestions": [
        "Gợi ý 1",
        "Gợi ý 2",
        "Gợi ý 3"
      ]
    }}
  ]
}}

Cách viết world_draft:
Nếu người dùng đưa ra ý tưởng, mở rộng trung thành với ý đó — đừng thay thế bằng thứ của bạn.
Nếu người dùng bỏ qua, tạo ra một thế giới gốc có hồn.
Viết như một nhà văn đang giới thiệu setting, không phải như một wiki entry.
Thế giới phải có điều gì đó khác lạ — một quy tắc kỳ dị, một mâu thuẫn ngầm, một điều không ai nói ra.

Cách viết questions:
Tạo 4 đến 6 câu hỏi. Mỗi câu hỏi phải cụ thể với thế giới vừa tạo — không hỏi chung chung.
Hỏi về nhân vật, xung đột trung tâm, giọng điệu, điều cấm kị của thế giới, hướng mở đầu.
Mỗi câu hỏi có 3 gợi ý, nhưng người dùng có thể trả lời tự do.

Ý tưởng thế giới từ người dùng:
{world_seed or "Người dùng bỏ qua. Hãy tự tạo một thế giới gốc."}
""".strip()


def build_novel_foundation_prompt(
    session: SessionState,
    player_name: str,
    gender: str | None,
    age: str | None,
    occupation: str | None,
    personality: str | None,
    answers: list[dict],
    target_words: int,
) -> str:
    return f"""
Bạn là nhà văn chính cho một tiểu thuyết tương tác AI.

NGÔN NGỮ: Toàn bộ nội dung người dùng thấy phải bằng tiếng Việt văn học, tự nhiên.

Nhiệm vụ:
Dựa trên bản thảo thế giới và câu trả lời của người chơi, hãy:
1. Viết hồ sơ tiểu thuyết — sổ tay tác giả để dùng cho các lượt sau.
2. Viết cảnh mở đầu của tiểu thuyết.
3. Tạo ba lựa chọn hướng đi phù hợp với tiểu thuyết.

Trả về ĐÚNG định dạng JSON sau. Không markdown, không giải thích ngoài JSON.

{{
  "foundation": "Văn xuôi tiếng Việt tổng hợp đầy đủ: thế giới, nhân vật chính, tuổi, giới tính, nghề nghiệp, tính cách, giọng điệu, xung đột trung tâm, quy tắc thế giới, tình huống xuất phát.",
  "novel_profile": {{
    "world_setting": "...",
    "genre": "...",
    "tone": "...",
    "protagonist": {{
      "name": "...",
      "age": "...",
      "gender": "...",
      "occupation": "...",
      "personality": "..."
    }},
    "main_conflict": "...",
    "world_rules": ["..."],
    "important_notes": ["..."]
  }},
  "story": "Cảnh mở đầu tiểu thuyết bằng tiếng Việt.",
  "choices": [
    "Hướng đi tường thuật dài hơn, có chiều sâu.",
    "Hướng đi tường thuật dài hơn, có chiều sâu.",
    "Hướng đi tường thuật dài hơn, có chiều sâu."
  ]
}}

Về novel_profile:
Đây là tài liệu tham chiếu nội bộ — không phải chỉ số game. Không có HP, inventory, level, hay cơ chế RPG.
Viết như một nhà văn ghi chú cho chính mình, không phải như một bảng thống kê.

Về phần story:
Bắt đầu ngay giữa một cảnh đang diễn ra — không giới thiệu bối cảnh, không kể lại quá khứ.
Để chi tiết cụ thể, cảm giác giác quan, và khoảnh khắc nội tâm dẫn người đọc vào.
Người chơi là đồng tác giả — không phải độc giả thụ động.
Độ dài gợi ý: khoảng {target_words} từ — nhưng dừng đúng lúc câu chuyện cần dừng.

Về choices:
Dài hơn lựa chọn game thông thường. Mô tả một hướng đi, một quyết định có trọng lượng. Không đánh số.

Bản thảo thế giới:
{session.world_summary or session.world_seed or "Không có bản thảo. Hãy tự tạo nền tảng hợp lý."}

Câu trả lời của người chơi:
{answers}

Nhân vật chính:
Tên: {player_name}
Giới tính: {gender or "tùy AI quyết định"}
Tuổi: {age or "tùy AI quyết định"}
Nghề nghiệp: {occupation or "tùy AI quyết định"}
Tính cách: {personality or "tùy AI quyết định"}
""".strip()


def build_turn_prompt(
    session: SessionState,
    recent_messages: list[Message],
    relevant_memories: list[MemoryChunk],
    player_input: str,
    target_words: int = 600,
    critical_instruction: str = "",
) -> str:
    structured_state_json = session.structured_state.model_dump_json(indent=2)
    rolling_summary = getattr(session, "rolling_story_summary", "")

    recent_text = "\n".join(
        [f"{m.role.upper()}: {m.content}" for m in recent_messages]
    ) or "None."

    memory_text = "\n".join(
        [f"- {m.text}" for m in relevant_memories]
    ) or "None."

    facts = "\n".join(
        [f"- {x}" for x in session.important_facts]
    ) or "None."

    mode = getattr(session, "mode", "adventure")
    novel_profile = getattr(session, "novel_profile", {}) or {}
    adventure_profile = getattr(session, "adventure_profile", {}) or {}
    is_novel = mode == "novel"

    if is_novel:
        writing_guidance = f"""
Bạn đang đồng sáng tác một tiểu thuyết tương tác với người chơi.

Viết như một nhà văn — không phải như một hệ thống trả lời câu hỏi.
Tiếp nối trực tiếp từ hành động hoặc lựa chọn của người chơi. Đừng tóm tắt lại những gì vừa xảy ra.
Để cảm xúc, không khí, và khoảnh lặng tự nhiên xuất hiện mà không cần giải thích.
Nhân vật không cần phải nói ra mọi suy nghĩ — đôi khi hành động im lặng hơn lời nói.
Duy trì tính nhất quán: thế giới, giọng điệu, tính cách nhân vật, và những gì đã xảy ra trước đó.
Đừng nhắc lại foundation hay giải thích lore — để nó hiện ra tự nhiên qua ngữ cảnh.
Tránh văn phong công thức. Không lặp lại cùng một nhịp cảnh: mô tả không gian → giải thích cảm xúc → quan sát người khác → câu hỏi nội tâm.
Không kết mỗi cảnh bằng một câu hỏi nội tâm kiểu "liệu... hay không" trừ khi thật sự cần thiết.
Không lạm dụng các cụm sáo mòn như "hít một hơi thật sâu", "cảm nhận được", "như thể", "bản giao hưởng", "một sức mạnh vô hình", "trái tim đập liên hồi".
Đừng giải thích tâm lý nhân vật nếu có thể cho thấy qua hành động, khoảng dừng, ánh mắt, cử chỉ, lời nói bị nuốt lại, hoặc lựa chọn né tránh.
Đối thoại phải tự nhiên về mặt xã hội. Một người lạ bí ẩn không nên nói như nhà tiên tri hoặc triết gia ngay lần gặp đầu, trừ khi bối cảnh đã tạo lý do rõ ràng.
Nhân vật phải hành động đúng với tính cách đã xây dựng. Nếu một nhân vật thận trọng làm điều liều lĩnh, phải có áp lực cụ thể khiến họ buộc phải làm vậy.
Foreshadowing phải kín. Đừng nói thẳng rằng nhân vật có "tiềm năng đặc biệt", "số phận", "năng lực ẩn", hay "khác biệt" quá sớm.
Tránh cảm giác anime/light novel nếu người chơi không yêu cầu. Viết như văn xuôi tiếng Việt được viết trực tiếp bằng tiếng Việt, không như bản dịch từ tiếng Anh hoặc Nhật.
Độ dài gợi ý: khoảng {target_words} từ — nhưng dừng đúng lúc cảnh cần dừng, dù ngắn hơn hay dài hơn.

Choices phải là những hướng tường thuật có trọng lượng, không phải lệnh điều khiển.
""".strip()
    else:
        writing_guidance = f"""
Bạn là người dẫn chuyện cho một cuộc phiêu lưu tương tác.

Tiếp nối trực tiếp từ hành động của người chơi. Thế giới phản ứng — đôi khi bất ngờ, đôi khi nguy hiểm, đôi khi im lặng một cách đáng sợ.
Viết cảnh đang diễn ra ngay lúc này — không kể lại quá khứ, không nhìn về tương lai quá xa.
Đừng nhắc lại foundation hay giải thích lore trực tiếp. Để nó hiện ra qua hành động, đối thoại, và chi tiết môi trường.
Thế giới có thể diễn biến bất ngờ, nhưng phải có logic nội tại. Nhân quả là mạch sống của câu chuyện.

Độ dài gợi ý: khoảng {target_words} từ.

Choices phải là hành động hoặc quyết định có thể xảy ra ngay trong khoảnh khắc hiện tại.
In Adventure Mode, this is a Survival Run. Choices should feel like immediate survival moves: scout, push forward, conserve supplies, negotiate, take a risk, retreat, tend wounds, or spend resources.
""".strip()

    if critical_instruction:
        writing_guidance += f"\n\nCRITICAL CONTEXT INSTRUCTION:\n{critical_instruction}"

    novel_section = f"""
=== HỒ SƠ TIỂU THUYẾT ===
{novel_profile}
""".strip() if is_novel else ""

    adventure_section = f"""
=== SURVIVAL RUN STATE ===
{adventure_profile}

Only Adventure Mode uses survival_update. Keep each pressure stat between 0 and 5. Bad stats should create consequences and recovery paths, not a hard game-over.
""".strip() if not is_novel else ""

    return f"""
NGÔN NGỮ: Toàn bộ nội dung người chơi thấy — tường thuật, đối thoại, không khí, lựa chọn — phải bằng tiếng Việt văn học, tự nhiên.

{writing_guidance}

Trả về ĐÚNG định dạng JSON sau. Không markdown, không giải thích ngoài JSON.

{{
  "story": "Đoạn tiếp theo của câu chuyện.",
  "choices": [
    "Lựa chọn 1",
    "Lựa chọn 2",
    "Lựa chọn 3"
  ],
  "survival_update": {{
    "danger": 3,
    "supplies": 3,
    "wounds": 0,
    "time_pressure": 3,
    "last_survival_note": "Short note about the current survival pressure."
  }}
}}

=== CHẾ ĐỘ ===
{mode}

{novel_section}

{adventure_section}

=== NỀN TẢNG CÂU CHUYỆN ===
{session.foundation_text}

=== TÓM TẮT THẾ GIỚI ===
{session.world_summary}

=== TÓM TẮT NHÂN VẬT ===
{session.character_summary}

=== STORY SUMMARY (Tóm tắt cốt truyện cục bộ) ===
{rolling_summary}

=== STRUCTURED FACTS (Sự kiện cốt lõi không thể thay đổi) ===
{structured_state_json}

=== RERANKED MEMORIES & NPC HISTORY (Ký ức liên quan) ===
{memory_text}

=== RECENT HISTORY (Raw Window) ===
{recent_text}

=== HÀNH ĐỘNG NGƯỜI CHƠI ===
{player_input}
""".strip()


def build_summary_prompt(
    session: SessionState,
    messages: list[Message],
) -> str:
    text = "\n".join(
        [f"{m.role}: {m.content}" for m in messages]
    )

    mode = getattr(session, "mode", "adventure")
    novel_profile = getattr(session, "novel_profile", {}) or {}

    if mode == "novel":
        return f"""
Bạn đang duy trì bộ nhớ dài hạn cho một tiểu thuyết tương tác AI.

NGÔN NGỮ: Toàn bộ nội dung tóm tắt phải bằng tiếng Việt súc tích.

Trả về ĐÚNG 4 mục dưới đây. Không JSON, không markdown, không giải thích.

WORLD_SUMMARY:
Tóm tắt ngắn gọn: bối cảnh thế giới, giọng điệu, quy tắc, xung đột lớn, địa điểm quan trọng, hệ thống chính trị hoặc siêu nhiên nếu có.

CHARACTER_SUMMARY:
Tóm tắt ngắn gọn: danh tính nhân vật chính, tính cách, vai trò, trạng thái cảm xúc hiện tại, các mối quan hệ, và những thay đổi trong hành trình.
Ghi lại cả những khoảnh khắc cảm xúc đáng nhớ — một quyết định khó, một lời nói bỏ lửng, một khoảnh lặng — không chỉ sự kiện bề mặt.

STORY_SUMMARY:
Tóm tắt ngắn gọn: các sự kiện chính, khám phá, xung đột, quyết định, hệ quả.
Ghi lại cả những gì chưa được giải quyết, những câu hỏi còn treo lơ lửng.

IMPORTANT_FACTS:
3 đến 8 sự kiện quan trọng bằng tiếng Việt, phân cách ĐÚNG bằng dấu chấm phẩy.

Hồ sơ tiểu thuyết:
{novel_profile}

Nền tảng câu chuyện:
{session.foundation_text}

Bộ nhớ trước đó:
WORLD_SUMMARY: {session.world_summary}
CHARACTER_SUMMARY: {session.character_summary}
STORY_SUMMARY: {session.story_summary}
IMPORTANT_FACTS: {'; '.join(session.important_facts)}

Tin nhắn mới:
{text}
""".strip()

    return f"""
Bạn đang duy trì bộ nhớ dài hạn cho một trò chơi phiêu lưu tương tác AI.

NGÔN NGỮ: Toàn bộ nội dung tóm tắt phải bằng tiếng Việt súc tích.

Trả về ĐÚNG 4 mục dưới đây. Không JSON, không markdown, không giải thích.

WORLD_SUMMARY:
Tóm tắt ngắn gọn: bối cảnh thế giới, giọng điệu, mối nguy hiểm, quy tắc quan trọng, phe phái hoặc địa điểm đáng chú ý.

CHARACTER_SUMMARY:
Tóm tắt ngắn gọn: danh tính nhân vật, vai trò, tính cách, động lực hiện tại, trạng thái cảm xúc.

STORY_SUMMARY:
Tóm tắt ngắn gọn: sự kiện quan trọng, khám phá, xung đột, hệ quả, tình huống hiện tại.
Những gì còn dang dở hoặc chưa rõ ràng cũng đáng ghi lại.

IMPORTANT_FACTS:
3 đến 8 sự kiện quan trọng bằng tiếng Việt, phân cách ĐÚNG bằng dấu chấm phẩy.

Nền tảng câu chuyện:
{session.foundation_text}

Bộ nhớ trước đó:
WORLD_SUMMARY: {session.world_summary}
CHARACTER_SUMMARY: {session.character_summary}
STORY_SUMMARY: {session.story_summary}
IMPORTANT_FACTS: {'; '.join(session.important_facts)}

Tin nhắn mới:
{text}
""".strip()


def build_memory_extract_prompt(message_text: str) -> str:
    return f"""
Bạn là hệ thống trích xuất ký ức cho một trò chơi phiêu lưu / tiểu thuyết tương tác AI.

Nhiệm vụ:
Đọc đoạn văn dưới đây. Trích xuất 1 đến 5 ký ức quan trọng cho bộ nhớ dài hạn.
Trả về định dạng JSON array chứa các object. Mỗi object đại diện cho 1 ký ức quan trọng.

Cấu trúc JSON yêu cầu:
[
  {{
    "text": "Nội dung ký ức (Tiếng Việt súc tích, 1 câu)",
    "location": "Địa điểm xảy ra (ví dụ: Rừng thông, Hang rồng, hoặc Unknown)",
    "involved_npcs": ["Tên NPC 1", "Tên NPC 2"],
    "keywords": ["từ khóa 1", "từ khóa 2", "từ khóa 3"]
  }}
]

Ưu tiên trích xuất: sự kiện có hậu quả, khám phá thế giới, thông tin NPC, quyết định quan trọng, thay đổi trạng thái quan hệ. Bỏ qua hội thoại rườm rà.
Nếu không có gì đáng lưu, trả về mảng rỗng [].
Chỉ trả về JSON hợp lệ.

Đoạn văn cần phân tích:
{message_text}
""".strip()

def build_structured_state_prompt(current_state_json: str, recent_messages_text: str) -> str:
    return f"""
Bạn là hệ thống theo dõi trạng thái cấu trúc (Structured State) của trò chơi.
Dưới đây là trạng thái hiện tại (JSON):
{current_state_json}

Và các diễn biến mới nhất:
{recent_messages_text}

Nhiệm vụ của bạn là CẬP NHẬT lại JSON trạng thái trên dựa vào diễn biến mới.
Đặc biệt lưu ý:
- Cập nhật current_location nếu người chơi di chuyển.
- Cập nhật current_quest nếu nhận nhiệm vụ mới hoặc hoàn thành.
- Nếu gặp NPC mới, thêm vào npcs. Nếu NPC cũ chết/mất tích, đổi status sang 'dead'/'missing'. Cập nhật relationship_score (-100 đến 100).
- Nếu có quyết định mang tính sinh tử/thay đổi cốt truyện, thêm vào critical_choices.
- Inventory và bosses_defeated (nếu chơi RPG mode).
- emotional_states và branching_flags (nếu chơi Novel mode).

Hãy trả về ĐÚNG CẤU TRÚC JSON GỐC với dữ liệu đã được cập nhật. Không thêm giải thích gì ngoài JSON.
""".strip()

def build_rolling_summary_prompt(current_summary: str, recent_messages: list) -> str:
    history_text = "\n".join([f"{'Người chơi' if m.role == 'user' else 'AI'}: {m.content}" for m in recent_messages])
    return f"""
Bạn là một thư ký ghi chép cốt truyện game. Nhiệm vụ của bạn là cập nhật bản tóm tắt cốt truyện liên tục.
Dưới đây là bản tóm tắt cốt truyện từ trước đến nay (Rolling Summary):
---
{current_summary if current_summary else "Chưa có sự kiện nào đáng kể."}
---

Dưới đây là các diễn biến (raw text) mới nhất vừa xảy ra:
---
{history_text}
---

Yêu cầu:
1. Viết lại một bản tóm tắt LIỀN MẠCH, bao gồm cả cốt truyện cũ và những diễn biến mới nhất.
2. Giữ lại các chi tiết mang tính nhân quả: tên NPC, quyết định quan trọng, thay đổi trạng thái, vật phẩm nhặt được.
3. Lược bỏ các chi tiết hội thoại rườm rà, tập trung vào sự phát triển của mạch truyện cốt lõi.
4. Viết bằng tiếng Việt, văn xuôi mạch lạc. KHÔNG dài quá 400 từ.

Chỉ trả về đoạn văn bản tóm tắt (không dùng Markdown block, không giải thích gì thêm).
""".strip()
