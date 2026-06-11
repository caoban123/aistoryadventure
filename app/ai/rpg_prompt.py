from __future__ import annotations
from typing import Any
from app.domain.models import SessionState, Message, MemoryChunk
from app.domain.rpg_models import RPGCharacter, RPGGameState

AETERNA_WORLD_LORE = """
Bối cảnh Sử thi Thế giới Aeterna:
1. Thần thoại Khởi nguyên: Thuở bình minh, lục địa Aeterna ngủ yên trong Đại Dương Vô Tận như viên ngọc thạch ngậm đầy ma pháp. Sự cân bằng hoàn hảo bị xé rách ở Kỷ Nguyên Thứ Nhất bởi một Vết Nứt Ma Pháp khổng lồ từ lỗi vũ trụ, chia đại lục thành 7 vùng đất lập thể cực đoan. Đồng thời đánh thức và đưa lối cho 8 chủng tộc: Con người (Human) kiên cường, Hoàng tộc (Royalty) kiêu hãnh, Tộc Tiên (Elf) thanh cao, Orc hung hãn, Goblin tinh ranh, Ác Quỷ (Devil) sa đọa, Thiên Thần (Angel) thánh khiết và những chiến binh Valkyrie huyền thoại.
2. Thảm họa Cổ Ngục và Chìa Khóa Vĩ Đại: Dòng ma pháp hắc ám tích tụ thành 7 Cổ Ngục (Dungeons) biệt lập sâu trong lòng đất, sinh ra 7 Đại Ma Thần (BOSS) tà ác mưu đồ hủy diệt trật tự thế giới. Hội đồng Tối cao Aeterna ban bố Sắc Lệnh Anh Hùng (Quests & Achievements). Theo huyền thoại cổ xưa, khi 7 Đại Ma Thần gục ngã dưới kiếm của Kẻ lữ hành định mệnh, mỗi Cổ Ngục hiến tế 1 Mảnh Vỡ Không Gian. Gom đủ 7 mảnh vỡ sẽ tự rèn nên Chiếc Chìa Khóa Vĩ Đại để mở Cổng Không Gian Hư Không – nơi ẩn thân của Final BOSS (kẻ thù tối cao đứng sau mọi sự diệt vong) cứu thế giới.
3. Chi tiết 7 vùng đất và Thủ hộ truyền kỳ:
  - Đồng Bằng Victoria: Nằm ở tâm điểm Aeterna, trù phú ngập tràn ánh nắng. Nơi ngự trị của tộc Human và Royalty với Vương Đô Victoria Gothic đá trắng nguy nga. Canh giữ nơi đây là Hoàng đế VinaVictoria (lớp Guard, thanh gươm vương quyền chẻ đôi bóng tối), bảo vệ lối vào Cổ Ngục Đồng Bằng.
  - Đồi Núi Sương Mù: Vùng núi đá và thung lũng sương mù hiểm trở ở phía Tây. Nơi sinh sống của tộc Angel trên đỉnh núi và hang ngục Devil dưới thung lũng sâu. Canh giữ bởi Đại pháp sư Wang (tộc Tiên, chiến binh Valkyrie lớp Caster ẩn cư bảo vệ Cổ Ngục Thung Lũng).
  - Đại Ngàn Londinium: Rừng mưa nhiệt đới bạt ngàn thánh địa của Elf. Cung điện Londinium bằng gỗ thánh tráng lệ ẩn sâu trong tán lá bạc ngàn. Cổ Ngục Đại Ngàn cắm rễ hấp thụ linh khí đất trời.
  - Biên Thùy Tro Tàn (Núi lửa & Vực thẳm): Vùng đất chết chóc bao trùm bởi khói bụi tàn tro và nham thạch nóng chảy, lãnh địa Devil, Orc, Goblin với Tòa Thành Chúa Quỷ. Canh giữ bởi bán quỷ đặc cấp Hoshiguma The Breacher (Valkyrie lớp Defender, tấm khiên khổng lồ trấn ngự dòng nham thạch bên Cổ Ngục Hỏa Ngục).
  - Bình Nguyên Cát: Hoang mạc và Sa mạc cát vàng oi bức của Orc và Goblin. Điểm nhấn là Thành Phố Tự Do – ốc đảo khổng lồ giao thương phi luật lệ cho mọi chủng tộc. Cổ Ngục Sa Mạc chôn vùi mảnh vỡ chìa khóa thứ năm.
  - Băng Nguyên Khởi Nguyên: Vùng cực bắc tuyết phủ trắng xóa và bão tuyết gầm rú quanh năm. Có Pháo Đài Bất Khả Xâm Phạm uy nghiêm của Thống soái trẻ tuổi SilverAsh the Reignfrost (Valkyrie lớp Guard, nội tại Kỷ Băng Hà đóng băng linh hồn địch, canh giữ Cổ Ngục Băng Giá).
  - Thánh Điện Thiên Giới: Thánh điện lơ lửng trên mây trắng, kiến trúc vàng ròng ngập ánh sáng vĩnh cửu của tộc Angel. Chánh Điện Thánh Đường Tối Cao được canh giữ bởi Lemuen (thiên thần đặc cấp, anh hùng Valkyrie lớp Sniper, canh giữ Cổ Ngục Thiên Giới).
""".strip()

def build_rpg_start_prompt(
    player_name: str,
    gender: str | None,
    region: str | None,
    objective: str | None,
    gold: int,
    equipment: dict[str, Any]
) -> str:
    """Builds the initial prompt to set up the RPG story."""
    region_str = region or "vùng đất kỳ bí quyết định bởi AI"
    objective_str = objective or "khám phá bí ẩn thế giới và sinh tồn"
    
    weapon_name = equipment.get("weapon", {}).get("name") if equipment.get("weapon") else "tay không"
    armor_name = equipment.get("armor", {}).get("name") if equipment.get("armor") else "áo vải thô sơ"

    return f"""
Bạn là người dẫn truyện chính cho một game nhập vai RPG text-based giả tưởng (Fantasy RPG) lấy bối cảnh tại lục địa Aeterna kỳ ảo.

[BỐI CẢNH THẾ GIỚI]:
{AETERNA_WORLD_LORE}

Nhiệm vụ:
Hãy viết chương mở đầu hành trình phiêu lưu cho nhân vật chính trong thế giới này. 
Nêu bật bối cảnh sử thi Aeterna, không khí kỳ bí và giới thiệu các chi tiết liên quan đến khu vực khởi hành.

Yêu cầu về ngôn ngữ:
- Phải viết bằng TIẾNG VIỆT văn học giàu cảm xúc, tự nhiên, cuốn hút, mang đậm chất sử thi anh hùng.
- Người chơi là nhân vật chính ("Bạn" hoặc đại từ phù hợp).
- Bắt đầu thẳng vào sự kiện, tránh dẫn nhập rườm rà.

Thông tin nhân vật chính:
- Tên: {player_name}
- Giới tính: {gender or "Nam"}
- Điểm xuất phát: {region_str}
- Mục tiêu: {objective_str}
- Hành trang ban đầu: {gold} Vàng, Vũ khí: {weapon_name}, Giáp: {armor_name}

Bạn BẮT BUỘC phải trả về cấu trúc JSON sau, KHÔNG thêm bất kỳ giải thích nào khác ngoài JSON:
{{
  "story": "Đoạn văn xuôi (2-4 đoạn) dẫn chuyện mở đầu chuyến phiêu lưu đầy lôi cuốn.",
  "choices": [
    "Lựa chọn khám phá 1 (ngắn gọn, dưới 15 từ)",
    "Lựa chọn khám phá 2 (ngắn gọn, dưới 15 từ)",
    "Lựa chọn khám phá 3 (ngắn gọn, dưới 15 từ)"
  ]
}}
""".strip()


def build_rpg_turn_prompt(
    session: SessionState,
    recent_messages: list[Message],
    relevant_memories: list[MemoryChunk],
    player_input: str,
    rpg_state_dict: dict[str, Any],
    event_type: str | None = None,
    event_context: str | None = None,
    offered_event: str | None = None
) -> str:
    """Builds prompt for a standard story turn or a special encounter."""
    
    # Format memories
    mem_str = "\n".join([f"- {m.text}" for m in relevant_memories])
    
    # Format history
    hist_str = ""
    for msg in recent_messages[-5:]:
        role_label = "Người chơi" if msg.role == "user" else "Người kể chuyện"
        hist_str += f"{role_label}: {msg.content}\n"

    # RPG Party information
    party_info = ""
    player_char = rpg_state_dict.get("player_character", {})
    party = rpg_state_dict.get("party", {})
    active_party = party.get("active", [])
    
    active_names = ", ".join([
        f"{c.get('name')} (Lớp: {c.get('char_class')}, Tộc: {c.get('race')}, HP: {c.get('stats', {}).get('hp')}/{c.get('stats', {}).get('max_hp')})"
        for c in active_party
    ])
    
    gold = rpg_state_dict.get("inventory", {}).get("gold", 0)
    turn_count = rpg_state_dict.get("turn_count", 0)

    # Context about the action
    action_context = ""
    if event_type == "monk":
        action_context = "SỰ KIỆN ĐẶC BIỆT: Gặp Tu sĩ ban phước. Người chơi chọn đi gặp tu sĩ. Hãy viết đoạn truyện người chơi bước vào đền thờ cổ kính hoặc gặp một vị tu sĩ hiền triết, được chữa lành vết thương và tặng nước thánh."
    elif event_type == "merchant":
        action_context = "SỰ KIỆN ĐẶC BIỆT: Gặp Thương nhân lang thang. Người chơi chọn gặp thương nhân bán đồ. Hãy viết câu chuyện người chơi bắt gặp một cỗ xe ngựa kỳ lạ hoặc quầy hàng bí ẩn của một thương nhân lém lỉnh."
    elif event_type == "stranger":
        stranger = rpg_state_dict.get("current_stranger", {})
        race = stranger.get("race", "Human")
        char_class = stranger.get("char_class", "Guard")
        rarity = stranger.get("rarity", "Common")
        gender = stranger.get("gender", "Male")
        action_context = f"SỰ KIỆN ĐẶC BIỆT: Gặp Kẻ lạ mặt. Nhân vật gặp: {gender == 'Female' and 'Nữ' or 'Nam'} {race} thuộc lớp {char_class} (Độ hiếm: {rarity}). Hãy viết câu chuyện chạm trán nhân vật này ở dọc đường đi. Họ có thể thân thiện hoặc cảnh giác."
    elif event_type == "item":
        action_context = "SỰ KIỆN ĐẶC BIỆT: Thu hoạch vật phẩm dọc đường. Hãy viết câu chuyện người chơi tìm thấy một chiếc rương cổ, tàn tích chiến trường hoặc ổ kho báu khuất sâu trong bụi rậm."
    elif offered_event:
        if offered_event == "monk":
            action_context = "SỰ KIỆN SẮP XẢY RA: Người chơi sắp bắt gặp một Tu sĩ ban phước. Hãy viết câu chuyện dẫn dắt để người chơi nhìn thấy bóng dáng một ngôi đền cổ kính hoặc một vị tu sĩ ở đằng xa. Hãy gợi ý sự gặp gỡ này trong câu chuyện. Trả về đúng 2 lựa chọn tiếp tục hành trình cho người chơi ở trường 'choices' (vì Lựa chọn 1 sẽ bị hệ thống tự động gán là lựa chọn đi gặp tu sĩ)."
        elif offered_event == "merchant":
            action_context = "SỰ KIỆN SẮP XẢY RA: Người chơi sắp bắt gặp một Thương nhân lang thang. Hãy viết câu chuyện dẫn dắt để người chơi phát hiện thấy một cỗ xe ngựa cũ kỹ hoặc một quầy hàng ven đường. Hãy gợi ý sự gặp gỡ này trong câu chuyện. Trả về đúng 2 lựa chọn tiếp tục hành trình cho người chơi ở trường 'choices' (vì Lựa chọn 1 sẽ bị hệ thống tự động gán là lựa chọn đi gặp thương nhân)."
        elif offered_event == "stranger":
            action_context = "SỰ KIỆN SẮP XẢY RA: Người chơi sắp bắt gặp một Kẻ lạ mặt. Hãy viết câu chuyện dẫn dắt để người chơi phát hiện thấy bóng người thấp thoáng ở phía trước. Hãy gợi ý sự gặp gỡ này trong câu chuyện. Trả về đúng 2 lựa chọn tiếp tục hành trình cho người chơi ở trường 'choices' (vì Lựa chọn 1 sẽ bị hệ thống tự động gán là lựa chọn đi gặp kẻ lạ mặt)."
        elif offered_event == "item":
            action_context = "SỰ KIỆN SẮP XẢY RA: Tìm thấy vật phẩm/chiếc rương. Hãy viết câu chuyện dẫn dắt để người chơi phát hiện thấy một chiếc rương cổ hoặc vật phẩm lấp lánh trong bụi rậm/vách đá. Hãy gợi ý sự gặp gỡ này trong câu chuyện. Trả về đúng 2 lựa chọn tiếp tục hành trình cho người chơi ở trường 'choices' (vì Lựa chọn 1 sẽ bị hệ thống tự động gán là lựa chọn thu thập vật phẩm)."
        elif offered_event.startswith("region:"):
            region_name = offered_event.split(":", 1)[1]
            action_context = f"SỰ KIỆN SẮP XẢY RA: Người chơi phát hiện thấy kiến trúc/địa điểm '{region_name}' ở phía trước. Hãy viết câu chuyện dẫn dắt để miêu tả vẻ kỳ vĩ hoặc bí ẩn của nơi này. Gợi ý sự khám phá địa điểm này trong câu chuyện. Trả về đúng 2 lựa chọn tiếp tục hành trình cho người chơi ở trường 'choices' (vì Lựa chọn 1 sẽ bị hệ thống tự động gán là lựa chọn tiến vào khám phá)."
        elif offered_event.startswith("dungeon:"):
            dungeon_name = offered_event.split(":", 1)[1]
            action_context = f"SỰ KIỆN SẮP XẢY RA: Người chơi phát hiện thấy lối vào hầm ngục '{dungeon_name}' u tối đầy nguy hiểm. Hãy viết câu chuyện dẫn dắt để miêu tả lối vào hầm ngục rùng rợn này. Gợi ý sự khám phá hầm ngục trong câu chuyện. Trả về đúng 2 lựa chọn tiếp tục hành trình cho người chơi ở trường 'choices' (vì Lựa chọn 1 sẽ bị hệ thống tự động gán là lựa chọn tiến vào hầm ngục)."
    else:
        action_context = f"Lượt chơi bình thường. Người chơi thực hiện hành động: '{player_input}'."

    curr_env = rpg_state_dict.get("environment", "")
    curr_reg = rpg_state_dict.get("current_region", "")
    reg_context = f"Bối cảnh hiện tại: Môi trường '{curr_env}'"
    if curr_reg:
        reg_context += f", cụ thể đang khám phá tại địa điểm/kiến trúc '{curr_reg}'"
    action_context = reg_context + ". " + action_context

    rolling_summary = getattr(session, "rolling_story_summary", "")
    structured_state_json = session.structured_state.model_dump_json(indent=2)

    choices_count_instruction = "trả về đúng 2 lựa chọn tránh/đi hướng khác" if offered_event else "tạo ra 3 lựa chọn tiếp theo"

    return f"""
Bạn là người dẫn chuyện (Dungeon Master) cho một game nhập vai RPG text-based giả tưởng (Fantasy RPG) lấy bối cảnh tại lục địa Aeterna kỳ ảo.

[WORLD LORE & HISTORY (Bối cảnh thế giới)]:
{AETERNA_WORLD_LORE}

NGÔN NGỮ: Toàn bộ câu chuyện phải bằng TIẾNG VIỆT văn học tự nhiên, cuốn hút, mang sắc thái sử thi kì ảo.

[STORY SUMMARY (Tóm tắt cốt truyện cục bộ)]:
{rolling_summary if rolling_summary else "Hành trình mới bắt đầu, chưa có sự kiện lịch sử."}

[STRUCTURED FACTS (Sự kiện cốt lõi không thể thay đổi)]:
{structured_state_json}

[RERANKED MEMORIES & NPC HISTORY (Ký ức liên quan)]:
{mem_str or "Không có ký ức cũ."}

[RECENT HISTORY (Raw Window)]:
{hist_str}

Trạng thái Game hiện tại:
- Lượt: {turn_count}
- Nhân vật chính: {player_char.get('name')} (HP: {player_char.get('stats', {}).get('hp')}/{player_char.get('stats', {}).get('max_hp')})
- Đội hình đồng hành hoạt động: {active_names}
- Vàng: {gold} Vàng

Ngữ cảnh sự kiện hiện tại:
{action_context}
{event_context or ""}

CHIẾN LƯỢC SÁNG TẠO & NHIỆM VỤ:
1. Tiếp tục dẫn dắt cốt truyện dựa trên lịch sử và sự kiện hiện tại. Không lặp lại những gì đã xảy ra.
2. Viết bằng tiếng Việt sinh động, chú trọng miêu tả giác quan, không khí thế giới RPG kỳ ảo.
3. [QUAN TRỌNG - PHÁ VỠ RẬP KHUÔN]: Đừng chỉ phản hồi thụ động hành động của người chơi. Bạn có quyền tự do sáng tạo cao nhất! Hãy thỉnh thoảng ném vào một biến cố bất ngờ (Plot twist), chướng ngại vật, hoặc một phát hiện bí ẩn để thế giới có vẻ rộng lớn và khó đoán hơn.
4. Nếu đây là lượt bình thường hoặc có sự kiện đề xuất sắp xảy ra, hãy {choices_count_instruction} cho người chơi.
5. Nếu đây là sự kiện đặc biệt đang hoạt động (monk/merchant/stranger/item), hãy viết câu chuyện dẫn nhập tự nhiên và có thể đưa các hành động cụ thể để người chơi tương tác vào trường 'choices'.

Trả về ĐÚNG định dạng JSON sau, không thêm bất kỳ văn bản nào ngoài JSON:
{{
  "story": "Văn bản dẫn chuyện bằng tiếng Việt (2-3 đoạn văn xuôi).",
  "choices": [
    "Lựa chọn 1 (ngắn gọn, dưới 15 từ)",
    "Lựa chọn 2 (ngắn gọn, dưới 15 từ)"
  ]
}}
""".strip()


def build_rpg_npc_description_prompt(character: RPGCharacter) -> str:
    """Prompt to generate short lore/background description for hired mercenaries or strangers."""
    gender_viet = "Nữ" if character.gender == "Female" else "Nam"
    return f"""
Bạn là một nhà biên kịch game RPG. 
Hãy viết một đoạn tiểu sử/mô tả ngắn (khoảng 2-3 câu, dưới 60 từ) bằng tiếng Việt cho nhân vật phụ sau:

Thông tin nhân vật:
- Tên: {character.name}
- Giới tính: {gender_viet}
- Chủng tộc: {character.race} (Valkyrie, Angel, Devil, Elf, Royalty, Orc, Goblin, Human)
- Lớp nhân vật: {character.char_class} (Defender, Guard, Caster, Sniper, Supporter)
- Độ hiếm: {character.rarity} (Mythic, Legendary, Epic, Rare, Uncommon, Common)

Đoạn văn cần làm nổi bật tính cách, ngoại hình hoặc một giai thoại nhỏ gắn liền với chủng tộc và lớp nhân vật của họ. Giọng điệu hào hùng, huyền bí hoặc hoang dã phù hợp thế giới RPG giả tưởng.

Chỉ trả về đoạn văn mô tả dạng chuỗi ký tự thường, không có tiêu đề hay định dạng gì khác.
""".strip()


def build_rpg_combat_narrative_prompt(combat_log: list[str]) -> str:
    """Prompt to summarize a turn-based combat round into a narrative paragraph."""
    log_str = "\n".join(combat_log)
    return f"""
Bạn là người tường thuật trận đấu trong một game RPG giả tưởng.
Dưới đây là biên bản (log) kỹ thuật của một hiệp đấu turn-based:

{log_str}

Nhiệm vụ:
Dựa trên các thông số kỹ thuật trên (sát thương gây ra, né đòn, buff/debuff, hồi máu, tử trận), hãy viết một đoạn văn xuôi tường thuật sinh động, đầy tính hành động bằng TIẾNG VIỆT (dưới 120 từ). 

Yêu cầu:
- Tả lại cảnh đụng độ giữa các nhân vật và kẻ địch một cách chân thực, đầy kịch tính.
- Tuyệt đối giữ nguyên kết quả của trận đấu (ai mất bao nhiêu máu, ai bị hạ gục, ai hồi máu...).
- Không hiển thị số liệu tính toán thô kiểu "xấp xỉ", "ATK", "RES" mà hãy chuyển thành văn cảnh như "nhát chém sấm sét", "phép thuật lửa", "khiên ánh sáng".

Chỉ trả về đoạn văn bản tường thuật, không có định dạng gì khác.
""".strip()


def build_rpg_suggest_names_prompt(gender: str) -> str:
    """Builds prompt to generate 4 fantasy names based on gender."""
    gender_viet = "Nữ" if gender == "Female" else ("Nam" if gender == "Male" else "Bất kỳ/Không xác định")
    return f"""
Bạn là nhà thiết kế trò chơi nhập vai giả tưởng (RPG).
Nhiệm vụ: Hãy đề xuất 4 tên nhân vật phù hợp cho một nhân vật chính trong thế giới giả tưởng cổ điển.
- Giới tính: {gender_viet}
- Phong cách: Kỳ ảo, anh hùng, thần thoại (ngầu, hợp chất RPG).

Trả về ĐÚNG định dạng JSON sau, không có bất kỳ giải thích nào khác ngoài JSON:
{{
  "names": [
    "Tên gợi ý 1",
    "Tên gợi ý 2",
    "Tên gợi ý 3",
    "Tên gợi ý 4"
  ]
}}
""".strip()


def build_rpg_suggest_objectives_prompt() -> str:
    """Builds prompt to generate 4 adventure objectives."""
    return f"""
Bạn là nhà thiết kế trò chơi nhập vai giả tưởng (RPG).
Nhiệm vụ: Hãy đề xuất 4 mục tiêu/nhiệm vụ phiêu lưu khởi đầu cho một người anh hùng mới bước chân vào thế giới kỳ ảo.
- Phong cách: Hấp dẫn, khơi gợi tò mò, thử thách sinh tồn hoặc cứu thế. Mỗi mục tiêu nên ngắn gọn (khoảng 5-12 từ, bằng tiếng Việt).

Trả về ĐÚNG định dạng JSON sau, không có bất kỳ giải thích nào khác ngoài JSON:
{{
  "objectives": [
    "Mục tiêu gợi ý 1",
    "Mục tiêu gợi ý 2",
    "Mục tiêu gợi ý 3",
    "Mục tiêu gợi ý 4"
  ]
}}
""".strip()


def build_rpg_suggest_appearance_prompt(player_name: str, gender: str, region: str, objective: str, gold: int, equipment_name: str) -> str:
    gender_viet = "Nữ" if gender == "Female" else ("Nam" if gender == "Male" else "Bất kỳ/Không xác định")
    return f"""
Bạn là nhà thiết kế trò chơi nhập vai giả tưởng (RPG).
Nhiệm vụ: Hãy đề xuất 1 đoạn mô tả ngoại hình ngắn gọn (khoảng 30-50 từ, bằng tiếng Việt) cho nhân vật chính của người chơi.
Thông tin nhân vật hiện có:
- Tên: {player_name}
- Giới tính: {gender_viet}
- Khu vực xuất thân: {region}
- Mục tiêu hành trình: {objective}
- Vàng ban đầu: {gold}
- Trang bị khởi đầu: {equipment_name}

Yêu cầu gợi ý ngoại hình:
- Phù hợp với giới tính, khu vực, trang bị khởi đầu và phong cách RPG kì ảo.
- Hãy tập trung mô tả các chi tiết trực quan như: mái tóc, trang phục, giáp trụ, vũ khí đang cầm, thần thái khuôn mặt hoặc tư thế đứng.
- Hãy trả về văn bản mô tả bằng tiếng Việt, dưới dạng một đoạn văn trôi chảy và sống động, không có danh sách, không có tiêu đề, không có bất kỳ giải thích nào khác ngoài đoạn văn đó.
""".strip()

