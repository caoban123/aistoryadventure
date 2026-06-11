import os

file_path = "d:/hcmus/HK4/Tư duy tính toán cho TTNT/final/aistoryadventure/app/services/rpg_engine.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

start_marker = "    @classmethod\n    def execute_action(cls, attacker: RPGCharacter, skill_name: str, target_id: str, combat_state: RPGCombatState, logs: list[str], acted_or_hit_ids: set[str] = None) -> None:"
end_marker = "    @classmethod\n    def check_combat_outcome"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1:
    print("Error: Could not find start marker!")
    exit(1)
if end_idx == -1:
    print("Error: Could not find end marker!")
    exit(1)

new_code = """    @classmethod
    def execute_action(cls, attacker: RPGCharacter, skill_name: str, target_id: str, combat_state: RPGCombatState, logs: list[str], acted_or_hit_ids: set[str] = None) -> None:
        \"\"\"Executes the specific attack or skill chosen by the player character with boss dodge/block checks.\"\"\"
        import re
        enemy = combat_state.enemy
        
        # Check enemy block/evasion for Golem, Ma vương Xương Cốt, and Alpha
        dodge_type = None
        if enemy and target_id == enemy.character_id:
            if enemy.name == "Golem" and random.random() < 0.20:
                dodge_type = "golem"
            elif enemy.name == "Ma vương Xương Cốt" and random.random() < 0.10:
                dodge_type = "skeleton"
            elif enemy.name == "Alpha" and enemy.stats.hp / enemy.stats.max_hp < 0.20 and random.random() < 0.20:
                dodge_type = "alpha"

        if dodge_type:
            # We want to run the action to spend energy/skills, but prevent damage
            old_enemy_hp = enemy.stats.hp
            temp_logs = []
            
            # Run the raw action logic
            cls._execute_action_raw(attacker, skill_name, target_id, combat_state, temp_logs, acted_or_hit_ids)
            
            # Restore enemy HP
            enemy.stats.hp = old_enemy_hp
            
            # Print dodge message
            if dodge_type == "golem":
                logs.append(f"🛡️ Golem kích hoạt kỹ năng đặc biệt: Chặn đứng hoàn toàn đòn đánh/chiêu thức từ {attacker.name}!")
            elif dodge_type == "skeleton":
                logs.append(f"💀 Ma vương Xương Cốt kích hoạt kỹ năng đặc biệt: Hóa hư vô, miễn nhiễm đòn đánh/chiêu thức từ {attacker.name}!")
            elif dodge_type == "alpha":
                logs.append(f"🌌 Alpha kích hoạt kỹ năng đặc biệt: Dịch chuyển hư không, né tránh hoàn toàn đòn đánh/chiêu thức từ {attacker.name}!")
                
            # Copy temp_logs to logs, modifying damage messages
            for log in temp_logs:
                # Replace "gây X sát thương" with "gây 0 sát thương (bị né/chặn)"
                log = re.sub(r"gây \\d+ sát thương", "gây 0 sát thương (bị né/chặn)", log)
                # Replace "hút X HP" with "hút 0 HP"
                log = re.sub(r"hút \\d+ HP", "hút 0 HP", log)
                # Replace HP display "Enemy HP: X/Y"
                log = re.sub(r"Enemy HP: \\d+/\\d+", f"Enemy HP: {old_enemy_hp}/{enemy.stats.max_hp}", log)
                logs.append(log)
        else:
            cls._execute_action_raw(attacker, skill_name, target_id, combat_state, logs, acted_or_hit_ids)

    @classmethod
    def _execute_action_raw(cls, attacker: RPGCharacter, skill_name: str, target_id: str, combat_state: RPGCombatState, logs: list[str], acted_or_hit_ids: set[str] = None) -> None:
        \"\"\"The original raw logic of execute_action (without dodge checking).\"\"\"
        enemy = combat_state.enemy
        if acted_or_hit_ids is not None:
            acted_or_hit_ids.add(attacker.character_id)
        old_enemy_hp = enemy.stats.hp if enemy else 0
        
        # 1. Basic Attack
        if skill_name == "basic_attack":
            if attacker.char_class == "Supporter":
                # Basic attack is a heal
                target = next((c for c in combat_state.combat_party if c.character_id == target_id), None)
                if not target or target.stats.hp <= 0:
                    logs.append(f"🚑 Trị thương thất bại: mục tiêu không hợp lệ hoặc đã tử trận.")
                    return
                # Heal amount = target_hp * (res / 100) -> Wait, let's use target_max_hp * (res / 100) or res %
                # Let's say: heals max(5, int(target.stats.max_hp * (attacker.stats.res / 100)))
                heal = max(5, int(target.stats.max_hp * (attacker.stats.res / 100)))
                target.stats.hp = min(target.stats.max_hp, target.stats.hp + heal)
                logs.append(f"🚑 {attacker.name} hồi phục {heal} HP cho {target.name} (HP: {target.stats.hp}/{target.stats.max_hp}).")
            else:
                # Normal attack
                # Check misses for Tê liệt (50% miss)
                if any(d.name == "Tê liệt" for d in attacker.debuffs) and random.random() < 0.50:
                    logs.append(f"💨 {attacker.name} bị tê liệt và đánh hụt đòn tấn công!")
                    return
                
                # Check evasion for Elf enemy
                if enemy.special_skills.passive_skill == "Uyển chuyển" and random.random() < 0.20:
                    logs.append(f"💨 {enemy.name} (Elf) nhanh nhẹn né tránh đòn tấn công cơ bản!")
                    return

                is_frozen = any(d.name == "Đông cứng" for d in enemy.debuffs)
                phys_dmg = int(attacker.stats.atk * (1 - enemy.stats.defense / 100))
                mag_dmg = int(attacker.stats.res * (1 - enemy.stats.res_def / 100))
                
                if is_frozen:
                    if attacker.name == "SilverAsh the Reignfrost":
                        phys_dmg = int(phys_dmg * 1.8)
                        logs.append(f"❄️ PHÁ BĂNG! SilverAsh gây x1.8 sát thương vật lý lên {enemy.name} đang bị đông cứng!")
                    else:
                        phys_dmg = int(phys_dmg * 1.5)
                        logs.append(f"❄️ PHÁ BĂNG! {attacker.name} gây x1.5 sát thương vật lý lên {enemy.name} đang bị đông cứng!")
                
                dmg = max(1, phys_dmg, mag_dmg)
                
                # Check shield buff on enemy
                has_shield = any(b.name == "Lá chắn" for b in enemy.buffs)
                if has_shield:
                    dmg = 0
                    # Remove shield
                    enemy.buffs = [b for b in enemy.buffs if b.name != "Lá chắn"]
                    logs.append(f"🛡️ {enemy.name} sử dụng Lá chắn hấp thụ hoàn toàn đòn tấn công cơ bản từ {attacker.name}!")
                else:
                    enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                    logs.append(f"⚔️ {attacker.name} tấn công thường gây {dmg} sát thương lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

        # 2. Skill 1
        elif skill_name == "skill_1":
            if attacker.special_skills.skill_1_countdown > 0:
                logs.append(f"⚠️ Chiêu thức 1 đang hồi ({attacker.special_skills.skill_1_countdown} lượt nữa)!")
                return
                
            # Defender Skill 1: Võ sĩ đạo
            if attacker.special_skills.skill_1 == "Võ sĩ đạo":
                attacker.special_skills.skill_1_activated = True
                attacker.special_skills.skill_1_countdown = 999  # 1 lần duy nhất
                
                alive_allies_count = sum(1 for c in combat_state.combat_party if c.stats.hp > 0)
                old_def = attacker.stats.defense
                old_max_hp = attacker.stats.max_hp
                hp_increase = int(old_def * old_max_hp / 100)
                
                RPGEngine.sync_character_stats(attacker, alive_allies_count)
                attacker.stats.hp = min(attacker.stats.max_hp, attacker.stats.hp + hp_increase)
                
                logs.append(f"🛡️ Hoshiguma kích hoạt 'Võ sĩ đạo' (1 lần duy nhất)! DEF giảm về 0, tăng Max_HP thêm {hp_increase} (HP hiện tại: {attacker.stats.hp}/{attacker.stats.max_hp}, DEF: 0).")
                
            # Guard Skill 1: Sư tử hống (50% sợ hãi + buff team)
            elif attacker.special_skills.skill_1 == "Sư tử hống":
                attacker.special_skills.skill_1_countdown = 8
                logs.append(f"🦁 {attacker.name} sử dụng 'Sư tử hống' gầm rú chấn động chiến trường!")
                
                # Buff team: Gia tăng sĩ khí (+5% stats, duration 2, excluding self)
                buffed_allies = []
                for char in combat_state.combat_party:
                    if char.stats.hp > 0 and char.character_id != attacker.character_id:
                        if not any(b.name == "Gia tăng sĩ khí" for b in char.buffs):
                            char.buffs.append(RPGBuff(name="Gia tăng sĩ khí", duration=2))
                            buffed_allies.append(char.name)
                if buffed_allies:
                    logs.append(f"✨ Đồng minh {', '.join(buffed_allies)} nhận buff 'Gia tăng sĩ khí' (+5% ATK/DEF/SPD) trong 2 lượt.")
                
                # Debuff enemy: 50% Fear (Sợ hãi, 3 turns)
                if random.random() < 0.50:
                    if any(b.name == "Lá chắn phép" for b in enemy.buffs):
                        logs.append(f"✨ {enemy.name} kháng hiệu ứng Sợ hãi nhờ Lá chắn phép.")
                    else:
                        enemy.debuffs.append(RPGDebuff(name="Sợ hãi", duration=3))
                        logs.append(f"😨 {enemy.name} hoảng sợ nhận hiệu ứng 'Sợ hãi' trong 3 lượt!")
                else:
                    logs.append(f"💨 {enemy.name} giữ vững ý chí, chống chịu được tiếng gầm.")

            # Guard Skill 1: Quét kiếm (SilverAsh)
            elif attacker.special_skills.skill_1 == "Quét kiếm":
                attacker.special_skills.skill_1_countdown = 3
                phys_dmg = int(0.80 * attacker.stats.atk * (1 - enemy.stats.defense / 100))
                is_frozen = any(d.name == "Đông cứng" for d in enemy.debuffs)
                if is_frozen:
                    phys_dmg = int(phys_dmg * 1.8)
                    logs.append(f"❄️ PHÁ BĂNG! SilverAsh quét kiếm gây x1.8 sát thương lên {enemy.name} đang bị đông cứng!")
                dmg = max(1, phys_dmg)
                
                # Check shield
                has_shield = any(b.name == "Lá chắn" for b in enemy.buffs)
                if has_shield:
                    enemy.buffs = [b for b in enemy.buffs if b.name != "Lá chắn"]
                    logs.append(f"🛡️ {enemy.name} sử dụng Lá chắn hấp thụ hoàn toàn sát thương Quét kiếm!")
                else:
                    enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                    if any(b.name == "Lá chắn phép" for b in enemy.buffs):
                        logs.append(f"✨ {enemy.name} kháng hiệu ứng Giá lạnh nhờ Lá chắn phép.")
                    else:
                        enemy.debuffs.append(RPGDebuff(name="Giá lạnh", duration=6))
                        logs.append(f"❄️ {attacker.name} quét kiếm gây {dmg} sát thương và để lại 1 tầng Giá lạnh lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                        
                        # Kích hoạt nội tại Kỷ băng hà ngay lập tức
                        frost_count = sum(1 for d in enemy.debuffs if d.name == "Giá lạnh")
                        if frost_count >= 2:
                            enemy.debuffs = [d for d in enemy.debuffs if d.name != "Giá lạnh"]
                            enemy.debuffs.append(RPGDebuff(name="Đông cứng", duration=1))
                            logs.append(f"❄️ Nội tại 'Kỷ băng hà' kích hoạt! Chuyển {frost_count} tầng Giá lạnh thành Đông cứng (1 lượt)!")
                            RPGEngine.sync_character_stats(enemy, 1)

            # Caster Skill 1: Vây hãm (đặt quân cờ/20% nổ)
            elif attacker.special_skills.skill_1 == "Vây hãm":
                attacker.special_skills.skill_1_countdown = 2
                
                # Check 20% explosion of the new piece
                exploded = random.random() < 0.20
                if exploded:
                    dmg = max(1, int(0.50 * attacker.stats.res * (1 - enemy.stats.res_def / 100)))
                    enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                    logs.append(f"💥 Quân cờ mới đặt phát nổ gây {dmg} sát thương ma pháp lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                else:
                    attacker.special_skills.quan_co_count += 1
                    logs.append(f"♟️ {attacker.name} đặt thêm 1 quân cờ lên sân (Tổng cộng: {attacker.special_skills.quan_co_count} quân cờ).")
                
                # 15% chance to double the total count of chess pieces (Passive Khai triển)
                if attacker.special_skills.passive_skill == "Khai triển" and random.random() < 0.15:
                    attacker.special_skills.quan_co_count *= 2
                    logs.append(f"🔮 Nội tại 'Khai triển' kích hoạt! Bộ đếm quân cờ tăng gấp đôi thành {attacker.special_skills.quan_co_count} quân.")

            # Sniper Skill 1: Khóa mục tiêu (auto firing mode setup)
            elif attacker.special_skills.skill_1 == "Khóa mục tiêu":
                if attacker.special_skills.bullet_count <= 0:
                    logs.append(f"⚠️ {attacker.name} không còn đạn để dùng chiêu Khóa mục tiêu!")
                    return
                
                attacker.special_skills.skill_1_activating = True
                attacker.special_skills.skill_1_countdown = 8
                
                # Sau khi kích hoạt Lemuen sẽ bắn ngay 1 viên đạn
                enemy = combat_state.enemy
                if enemy and enemy.stats.hp > 0:
                    dmg = max(1, int(random.uniform(0.60, 1.00) * attacker.stats.atk * (1 - enemy.stats.defense / 100)))
                    enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                    attacker.special_skills.bullet_count -= 1
                    logs.append(f"🎯 Lemuen kích hoạt 'Khóa mục tiêu'! Khởi động trạng thái khóa mục tiêu và bắn ngay 1 viên đạn gây {dmg} sát thương lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}, Số đạn còn lại: {attacker.special_skills.bullet_count}).")
                    cls.check_and_trigger_death(enemy, combat_state, logs)
                    
                    if attacker.special_skills.bullet_count <= 0:
                        attacker.special_skills.skill_1_activating = False
                        logs.append(f"🎯 Lemuen đã bắn hết đạn Khóa mục tiêu, kết thúc trạng thái khóa.")

            # Angel Skill 1: Lá chắn (buff Angel + 1 target ally, duration=2)
            elif attacker.special_skills.skill_1 == "Lá chắn":
                attacker.special_skills.skill_1_countdown = 5
                target = next((c for c in combat_state.combat_party if c.character_id == target_id and c.stats.hp > 0), None)
                
                if not target or target.character_id == attacker.character_id:
                    other_allies = [c for c in combat_state.combat_party if c.character_id != attacker.character_id and c.stats.hp > 0]
                    if other_allies:
                        target = other_allies[0]
                        
                shielded = [attacker]
                if target:
                    shielded.append(target)
                
                for char in shielded:
                    char.buffs = [b for b in char.buffs if b.name != "Lá chắn"]
                    char.buffs.append(RPGBuff(name="Lá chắn", duration=2))
                
                names = " & ".join([c.name for c in shielded])
                logs.append(f"🛡️ Angel ban phước 'Lá chắn' bảo hộ cho {names} trong 2 lượt.")

            # Devil Skill 1: Hấp thụ (hút 15% HP target)
            elif attacker.special_skills.skill_1 == "Hấp thụ":
                attacker.special_skills.skill_1_countdown = 4
                
                target = next((c for c in combat_state.combat_party if c.character_id == target_id), None)
                if not target or target.stats.hp <= 0:
                    target = enemy
                    
                dmg = int(target.stats.hp * 0.15)
                if target.character_id != enemy.character_id:
                    target.stats.hp = max(1, target.stats.hp - dmg)
                    logs.append(f"😈 Devil kích hoạt 'Hấp thụ', hút {dmg} HP từ đồng đội {target.name} (HP của {target.name} còn lại: {target.stats.hp}).")
                else:
                    target.stats.hp = max(0, target.stats.hp - dmg)
                    logs.append(f"😈 Devil kích hoạt 'Hấp thụ', hút {dmg} HP từ kẻ địch {target.name} (Enemy HP: {target.stats.hp}).")
                    
                attacker.stats.hp = min(attacker.stats.max_hp, attacker.stats.hp + dmg)
                logs.append(f"😈 HP của Devil tăng lên: {attacker.stats.hp}/{attacker.stats.max_hp}.")

            # Elf Skill 1: Mưa tên (+20%SPD, 2-5 mũi tên chuẩn)
            elif attacker.special_skills.skill_1 == "Mưa tên":
                attacker.special_skills.skill_1_countdown = 4
                attacker.buffs.append(RPGBuff(name="Tăng tốc", duration=1))
                
                arrows = random.randint(2, 5)
                total_dmg = 0
                for _ in range(arrows):
                    dmg = max(1, int(0.20 * attacker.stats.atk))
                    total_dmg += dmg
                    
                enemy.stats.hp = max(0, enemy.stats.hp - total_dmg)
                logs.append(f"🏹 Elf bắn liên hoàn 'Mưa tên' ({arrows} mũi tên) gây tổng {total_dmg} sát thương chuẩn lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                
                attacker.debuffs.append(RPGDebuff(name="Sơ hở", duration=1))
                logs.append(f"⚠️ {attacker.name} lâm vào trạng thái sơ hở, nhận thêm 20% sát thương từ đòn đánh tiếp theo trong lượt này.")

            # Royalty Skill 1: Phong tước (hy sinh 50% HP reset CD 1 đồng minh chỉ định)
            elif attacker.special_skills.skill_1 == "Phong tước":
                attacker.special_skills.skill_1_countdown = 999  # 1 lần duy nhất
                
                hp_loss = int(attacker.stats.hp * 0.50)
                attacker.stats.hp = max(1, attacker.stats.hp - hp_loss)
                
                target = next((c for c in combat_state.combat_party if c.character_id == target_id), None)
                if target:
                    target.special_skills.skill_1_countdown = 0
                    target.special_skills.skill_2_countdown = 0
                    logs.append(f"👑 Royalty hiến tế {hp_loss} HP của bản thân để phong tước cho {target.name}, làm mới toàn bộ thời gian hồi chiêu của nhân vật này! (Royalty HP: {attacker.stats.hp}/{attacker.stats.max_hp})")
                else:
                    logs.append(f"👑 Royalty hiến tế {hp_loss} HP nhưng không tìm thấy đồng đội hợp lệ.")

        # 3. Skill 2
        elif skill_name == "skill_2":
            if attacker.special_skills.skill_2_countdown > 0:
                logs.append(f"⚠️ Chiêu thức 2 đang hồi ({attacker.special_skills.skill_2_countdown} lượt nữa)!")
                return
                
            # Defender Skill 2: Hoả liên trảm quỷ (6 chém ma pháp)
            if attacker.special_skills.skill_2 == "Hoả liên trảm quỷ":
                attacker.special_skills.skill_2_countdown = 10
                logs.append(f"🔥 {attacker.name} kích hoạt 'Hoả liên trảm quỷ', chém 6 nhát kiếm lửa cuồng bạo và kích hoạt Bất tử trong lượt này!")
                
                attacker.buffs.append(RPGBuff(name="Bất tử", duration=1))
                
                total_dmg = 0
                total_heal = 0
                for i in range(6):
                    hp_lost = attacker.stats.max_hp - attacker.stats.hp
                    dmg = max(1, int(0.60 * hp_lost * (1 - enemy.stats.res_def / 100))) if hp_lost > 0 else 0
                    heal = int(0.05 * hp_lost)
                    
                    enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                    attacker.stats.hp = min(attacker.stats.max_hp, attacker.stats.hp + heal)
                    total_dmg += dmg
                    total_heal += heal
                
                logs.append(f"💥 6 nhát chém lửa phép gây tổng {total_dmg} sát thương phép lên {enemy.name} và hồi {total_heal} HP cho Hoshiguma (Hoshiguma HP: {attacker.stats.hp}/{attacker.stats.max_hp}, Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Guard Skill 2: Phán quyết cuối cùng (60%ATK chuẩn + 40%ATK vật lý)
            elif attacker.special_skills.skill_2 == "Phán quyết cuối cùng":
                attacker.special_skills.skill_2_countdown = 6
                true_dmg = int(attacker.stats.atk * 0.60)
                phys_dmg = int(attacker.stats.atk * 0.40 * (1 - enemy.stats.defense / 100))
                
                crit_triggered = random.random() < 0.20
                crit_dmg = 0
                if crit_triggered:
                    crit_dmg = int(attacker.stats.atk * 0.30)
                
                dmg = max(1, true_dmg + phys_dmg + crit_dmg)
                enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                
                crit_msg = f" (🔥 BẠO KÍCH! +{crit_dmg} sát thương chuẩn)" if crit_triggered else ""
                logs.append(f"⚖️ VinaVictoria hành quyết 'Phán quyết cuối cùng' gây {dmg} sát thương ({true_dmg} chuẩn + {phys_dmg} vật lý{crit_msg}) lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Guard Skill 2: Băng tuyết vũ (SilverAsh - chém 5 nhát vật lý)
            elif attacker.special_skills.skill_2 == "Băng tuyết vũ":
                attacker.special_skills.skill_2_countdown = 8
                logs.append(f"❄️ {attacker.name} kích hoạt 'Băng tuyết vũ', thi triển 5 nhát kiếm chớp nhoáng xé toạc không gian!")
                
                total_dmg = 0
                for i in range(5):
                    # Check né đòn Elf
                    if enemy.special_skills.passive_skill == "Uyển chuyển" and random.random() < 0.20:
                        logs.append(f"   💨 Nhát chém {i+1}: {enemy.name} né tránh thành công!")
                        continue
                        
                    is_frozen = any(d.name == "Đông cứng" for d in enemy.debuffs)
                    phys_dmg = int(attacker.stats.atk * (1 - enemy.stats.defense / 100))
                    
                    if is_frozen:
                        phys_dmg = int(phys_dmg * 1.8)
                        logs.append(f"   ❄️ Nhát chém {i+1}: Gây {phys_dmg} sát thương vật lý lên mục tiêu Đông cứng (x1.8)!")
                    else:
                        logs.append(f"   ⚔️ Nhát chém {i+1}: Gây {phys_dmg} sát thương vật lý.")
                    
                    # Check shield
                    has_shield = any(b.name == "Lá chắn" for b in enemy.buffs)
                    if has_shield:
                        enemy.buffs = [b for b in enemy.buffs if b.name != "Lá chắn"]
                        logs.append(f"      🛡️ Bị Lá chắn của {enemy.name} cản lại!")
                    else:
                        enemy.stats.hp = max(0, enemy.stats.hp - phys_dmg)
                        total_dmg += phys_dmg
                        cls.check_and_trigger_death(enemy, combat_state, logs)
                        if enemy.stats.hp <= 0:
                            break
                            
                logs.append(f"💥 Băng tuyết vũ gây tổng cộng {total_dmg} sát thương vật lý lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Caster Skill 2: Chiếu tướng (30%*count*RES ma pháp)
            elif attacker.special_skills.skill_2 == "Chiếu tướng":
                if attacker.special_skills.quan_co_count == 0:
                    logs.append(f"⚠️ Không có quân cờ nào trên bàn cờ để kích hoạt Chiếu tướng!")
                    return
                attacker.special_skills.skill_2_countdown = 10
                count = attacker.special_skills.quan_co_count
                
                dmg = int(0.30 * count * attacker.stats.res * (1 - enemy.stats.res_def / 100))
                dmg = max(1, dmg)
                
                enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                attacker.special_skills.quan_co_count = 0
                logs.append(f"♟️ Vương cờ kích hoạt 'Chiếu tướng' bùng nổ {count} quân cờ gây {dmg} sát thương ma pháp lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Sniper Skill 2: Khai hoả toàn diện (bắn hết đạn)
            elif attacker.special_skills.skill_2 == "Khai hoả toàn diện":
                if attacker.special_skills.bullet_count == 0:
                    logs.append(f"⚠️ {attacker.name} không còn đạn để kích hoạt Khai hoả toàn diện!")
                    return
                attacker.special_skills.skill_2_countdown = 10
                bullets = attacker.special_skills.bullet_count
                attacker.special_skills.bullet_count = 0
                
                logs.append(f"🔫 Lemuen kích hoạt 'Khai hoả toàn diện', dội bão tên lửa gồm {bullets} viên đạn thường kèm 1 viên đặc biệt!")
                
                total_dmg = 0
                for i in range(bullets):
                    mult = random.uniform(0.80, 1.90)
                    dmg = max(1, int(mult * attacker.stats.atk * (1 - enemy.stats.defense / 100)))
                    total_dmg += dmg
                    logs.append(f"   🚀 Tên lửa {i+1}: gây {dmg} sát thương vật lý.")
                
                # Special bullet
                special_mult = random.uniform(1.00, 3.00)
                special_dmg = max(1, int(special_mult * attacker.stats.atk * (1 - enemy.stats.defense / 100)))
                total_dmg += special_dmg
                logs.append(f"   🔥 Tên lửa đặc biệt: gây {special_dmg} sát thương vật lý.")
                
                enemy.stats.hp = max(0, enemy.stats.hp - total_dmg)
                logs.append(f"💥 Khai hoả toàn diện gây tổng cộng {total_dmg} sát thương lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Angel Skill 2: Thiên lôi (30 chuẩn, 30% tê liệt)
            elif attacker.special_skills.skill_2 == "Thiên lôi":
                attacker.special_skills.skill_2_countdown = 3
                dmg = 30
                enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                logs.append(f"⚡ Angel triệu hồi 'Thiên lôi' giáng xuống {dmg} sát thương chuẩn lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                if random.random() < 0.30:
                    enemy.debuffs.append(RPGDebuff(name="Tê liệt", duration=2))
                    logs.append(f"⚡ {enemy.name} trúng lôi đình bị 'Tê liệt' trong 2 lượt!")

            # Devil Skill 2: Huyết quỷ thuật (lấy máu team + bùng nổ)
            elif attacker.special_skills.skill_2 == "Huyết quỷ thuật":
                attacker.special_skills.skill_2_countdown = 6
                hp_pool = 0
                
                # Take 20% current HP from other allies
                for char in combat_state.combat_party:
                    if char.character_id != attacker.character_id and char.stats.hp > 0:
                        lost = int(char.stats.hp * 0.20)
                        char.stats.hp = max(1, char.stats.hp - lost)
                        hp_pool += lost
                        logs.append(f"🩸 Devil rút {lost} HP của đồng đội {char.name} làm vật tế.")
                
                # Take 30% current HP of self
                self_lost = int(attacker.stats.hp * 0.30)
                attacker.stats.hp = max(1, attacker.stats.hp - self_lost)
                hp_pool += self_lost
                logs.append(f"🩸 Devil hiến tế {self_lost} HP của bản thân.")
                
                dmg = max(1, int(hp_pool * (1 - enemy.stats.res_def / 100)))
                enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                logs.append(f"🩸 Devil bùng nổ quả cầu Huyết Quỷ gây {dmg} sát thương phép lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                
                if random.random() < 0.30:
                    if any(b.name == "Lá chắn phép" for b in enemy.buffs):
                        logs.append(f"✨ {enemy.name} kháng hiệu ứng Thiêu đốt nhờ Lá chắn phép.")
                    else:
                        enemy.debuffs.append(RPGDebuff(name="Thiêu đốt", duration=5))
                        logs.append(f"🔥 {enemy.name} trúng huyết hỏa nhận hiệu ứng 'Thiêu đốt' trong 5 lượt!")

        # If enemy took damage, register it
        if enemy and enemy.stats.hp < old_enemy_hp and acted_or_hit_ids is not None:
            acted_or_hit_ids.add(enemy.character_id)

        # Recalculate stats in case HP/buff modifications happened
        alive_allies_count = sum(1 for c in combat_state.combat_party if c.stats.hp > 0)
        RPGEngine.sync_character_stats(attacker, alive_allies_count)
        RPGEngine.sync_character_stats(enemy, 1)

    @classmethod
    def enemy_turn(cls, combat_state: RPGCombatState, defender_id: str | None, logs: list[str], acted_or_hit_ids: set[str] = None) -> None:
        \"\"\"Executes the automatic enemy action with custom Elite Boss & Alpha skills.\"\"\"
        enemy = combat_state.enemy
        if not enemy or enemy.stats.hp <= 0:
            return

        # Check if enemy is stunned / feared / frozen
        is_stunned = any(d.name in ["Choáng", "Sợ hãi", "Đông cứng"] for d in enemy.debuffs)
        if is_stunned:
            logs.append(f"💤 {enemy.name} bị khống chế (Choáng/Sợ hãi/Đông cứng), không thể hành động lượt này!")
            return

        if acted_or_hit_ids is not None:
            acted_or_hit_ids.add(enemy.character_id)

        # Determine target: Hoshiguma intercepts first. Else, select a target.
        target = None
        
        # Check if Hoshiguma (Valkyrie Defender) is alive in party (hp > 0 and not failed revival)
        hoshi = next((c for c in combat_state.combat_party if c.name == "Hoshiguma the breacher" and c.stats.hp > 0), None)
        
        if hoshi:
            target = hoshi
            logs.append(f"🛡️ Hoshiguma khiêu khích kẻ địch! {enemy.name} buộc phải hướng đòn tấn công vào cô.")
        else:
            # Random target
            alive_allies = [c for c in combat_state.combat_party if c.stats.hp > 0]
            if not alive_allies:
                return
            target = random.choice(alive_allies)

        # Apply defender shielding if player set a defender and it's not the target
        if not hoshi and defender_id and defender_id != target.character_id:
            defender = next((c for c in combat_state.combat_party if c.character_id == defender_id and c.stats.hp > 0), None)
            if defender:
                # Roll shield success
                def_chance = DEFEND_CHANCES.get(defender.char_class, 20)
                # Apply Tê liệt block penalty on defender
                if any(d.name == "Tê liệt" for d in defender.debuffs):
                    def_chance = 0 # Cannot defend if paralyzed
                    logs.append(f"💨 {defender.name} bị tê liệt nên không thể thực hiện đỡ đòn đỡ hộ!")
                
                if def_chance > 0 and random.uniform(0, 100) <= def_chance:
                    logs.append(f"🛡️ {defender.name} đã đỡ đòn thành công bảo vệ {target.name}!")
                    target = defender
                else:
                    logs.append(f"💨 {defender.name} cố gắng đỡ đòn bảo vệ {target.name} nhưng thất bại!")

        # Execute Enemy Attack
        is_frozen = any(d.name == "Đông cứng" for d in target.debuffs)
        phys_dmg = int(enemy.stats.atk * (1 - target.stats.defense / 100))
        mag_dmg = int(enemy.stats.res * (1 - target.stats.res_def / 100))
        
        if is_frozen:
            if enemy.name == "SilverAsh the Reignfrost":
                phys_dmg = int(phys_dmg * 1.8)
                logs.append(f"❄️ PHÁ BĂNG! SilverAsh của kẻ địch gây x1.8 sát thương vật lý lên {target.name} đang bị đông cứng!")
            else:
                phys_dmg = int(phys_dmg * 1.5)
                logs.append(f"❄️ PHÁ BĂNG! {enemy.name} gây x1.5 sát thương vật lý lên {target.name} đang bị đông cứng!")
                
        dmg = max(1, phys_dmg, mag_dmg)
        
        # Elite Boss Custom Attack Modifiers: WereWolf, Poseidon, Alpha
        if enemy.name == "WereWolf" and enemy.stats.hp / enemy.stats.max_hp < 0.20 and random.random() < 0.20:
            dmg = dmg * 2
            logs.append(f"💥 WereWolf phẫn nộ kích hoạt 'Cuồng loạn' chém x2 sát thương!")
        elif enemy.name == "Poseidon" and random.random() < 0.30:
            dmg = dmg * 2
            logs.append(f"🌊 Poseidon vung đinh ba vạn cân đánh x2 sát thương!")
        elif enemy.name == "Alpha" and random.random() < 0.10:
            dmg = dmg * 3
            logs.append(f"🌌 Alpha vung trường thương đen kích hoạt đánh x3 sát thương!")

        # Apply Elf Mưa tên negative modifier (Sơ hở debuff)
        has_so_ho = any(d.name == "Sơ hở" for d in target.debuffs)
        if has_so_ho:
            dmg = int(dmg * 1.20)
            
        # Check shield on target
        has_shield = any(b.name == "Lá chắn" for b in target.buffs)
        if has_shield:
            dmg = 0
            target.buffs = [b for b in target.buffs if b.name != "Lá chắn"]
            logs.append(f"🛡️ {target.name} chặn hoàn toàn sát thương nhờ Lá chắn!")
        else:
            target.stats.hp = max(0, target.stats.hp - dmg)
            so_ho_msg = " (trúng Sơ hở +20%)" if has_so_ho else ""
            logs.append(f"💥 Kẻ địch {enemy.name} tấn công gây {dmg} sát thương{so_ho_msg} lên {target.name} (HP: {target.stats.hp}/{target.stats.max_hp}).")
            
            if dmg > 0:
                if acted_or_hit_ids is not None:
                    acted_or_hit_ids.add(target.character_id)
                # Check Hoshiguma passive interruption
                if target.special_skills.passive_skill == "Ma thần bất diệt" and target.special_skills.hoshi_passive_countdown > 0:
                    target.special_skills.hoshi_passive_countdown = -1
                    logs.append(f"💥 Hoshiguma đang trong quá trình hồi sinh nhưng nhận sát thương, 'Ma thần bất diệt' bị hủy bỏ hoàn toàn!")
            
            # Elite Boss & Alpha Debuffs & Healing/Lifesteal
            if target.stats.hp > 0:
                has_magic_shield = any(b.name == "Lá chắn phép" for b in target.buffs)
                if has_magic_shield:
                    logs.append(f"✨ {target.name} kháng hoàn toàn hiệu ứng bất lợi từ kẻ địch nhờ Lá chắn phép.")
                else:
                    if enemy.name == "Medusa":
                        if random.random() < 0.20:
                            target.debuffs.append(RPGDebuff(name="Tê liệt", duration=2))
                            logs.append(f"🤢 {target.name} bị tê liệt bởi ánh nhìn của Medusa!")
                        if random.random() < 0.10:
                            target.debuffs.append(RPGDebuff(name="Chảy máu", duration=3))
                            logs.append(f"🤢 {target.name} bị chảy máu bởi nọc độc Medusa!")
                    elif enemy.name == "Vua Goblin":
                        if random.random() < 0.30:
                            target.debuffs.append(RPGDebuff(name="Chảy máu", duration=3))
                            logs.append(f"🤢 {target.name} bị chảy máu bởi đại đao của Vua Goblin!")
                    elif enemy.name == "WereWolf":
                        if enemy.stats.hp / enemy.stats.max_hp >= 0.20 and random.random() < 0.10:
                            target.debuffs.append(RPGDebuff(name="Chảy máu", duration=3))
                            logs.append(f"🤢 {target.name} bị cào rách vai, nhận hiệu ứng Chảy máu!")
                    elif enemy.name == "Dracula":
                        if random.random() < 0.10:
                            target.debuffs.append(RPGDebuff(name="Chảy máu", duration=3))
                            logs.append(f"🤢 {target.name} bị cắn chảy máu xối xả!")
                    elif enemy.name == "Golem":
                        if random.random() < 0.10:
                            target.debuffs.append(RPGDebuff(name="Choáng", duration=1))
                            logs.append(f"🤢 {target.name} bị chấn động mạnh dẫn đến Choáng!")
                    elif enemy.name == "Diablo":
                        if random.random() < 0.20:
                            target.debuffs.append(RPGDebuff(name="Thiêu đốt", duration=3))
                            logs.append(f"🤢 {target.name} bị thiêu đốt bởi ngọn lửa Địa Ngục của Diablo!")
                    elif enemy.name == "Thiên Dực Long Vương":
                        if random.random() < 0.20:
                            target.debuffs.append(RPGDebuff(name="Tê liệt", duration=2))
                            logs.append(f"🤢 {target.name} bị dòng điện của Thiên Dực Long Vương làm tê liệt!")
                    elif enemy.name == "Ma vương Xương Cốt":
                        if random.random() < 0.20:
                            target.debuffs.append(RPGDebuff(name="Chảy máu", duration=3))
                            logs.append(f"🤢 {target.name} bị chảy máu do kiếm khí hắc ám!")
                    elif enemy.name == "Alpha":
                        if random.random() < 0.30:
                            possible_debuffs = ["Chảy máu", "Thiêu đốt", "Tê liệt", "Choáng", "Chậm chạp", "Yếu đuối", "Sợ hãi", "Giá lạnh"]
                            debuff_name = random.choice(possible_debuffs)
                            duration = 2 if debuff_name in ["Choáng", "Tê liệt"] else 3
                            target.debuffs.append(RPGDebuff(name=debuff_name, duration=duration))
                            logs.append(f"🤢 Alpha áp đặt quyền năng hư không, {target.name} chịu hiệu ứng {debuff_name}!")
                    else:
                        debuff_data = ENEMY_DEBUFF_CHANCE.get(enemy.race, {"chance": 0, "debuffs": []})
                        if debuff_data["chance"] > 0 and random.uniform(0, 100) <= debuff_data["chance"]:
                            debuff_name = random.choice(debuff_data["debuffs"])
                            target.debuffs.append(RPGDebuff(name=debuff_name, duration=3))
                            logs.append(f"🤢 {target.name} chịu tác động xấu '{debuff_name}'!")

            # Lifesteal check for Dracula, Diablo, Alpha
            if enemy.stats.hp > 0:
                heal = 0
                if enemy.name == "Dracula" and random.random() < 0.20:
                    heal = int((enemy.stats.max_hp - enemy.stats.hp) * 0.20)
                    logs.append(f"🧛 Dracula hút máu kẻ địch hồi phục {heal} HP!")
                elif enemy.name == "Diablo" and random.random() < 0.10:
                    heal = int((enemy.stats.max_hp - enemy.stats.hp) * 0.30)
                    logs.append(f"😈 Diablo hút hồn hồi phục {heal} HP!")
                elif enemy.name == "Alpha" and random.random() < 0.10:
                    heal = int((enemy.stats.max_hp - enemy.stats.hp) * 0.40)
                    logs.append(f"🌌 Alpha đảo ngược thời gian hồi phục {heal} HP!")

                if heal > 0:
                    enemy.stats.hp = min(enemy.stats.max_hp, enemy.stats.hp + heal)
                    RPGEngine.sync_character_stats(enemy, 1)

            # Splash damage check for Thiên Dực Long Vương
            if enemy.name == "Thiên Dực Long Vương" and random.random() < 0.10:
                other_allies = [c for c in combat_state.combat_party if c.character_id != target.character_id and c.stats.hp > 0]
                if other_allies:
                    other = random.choice(other_allies)
                    splash = int(dmg * 0.50)
                    other.stats.hp = max(0, other.stats.hp - splash)
                    logs.append(f"🔥 Thiên Dực Long Vương quật đuôi gây {splash} sát thương lan lên {other.name}!")
                    cls.check_and_trigger_death(other, combat_state, logs)
                    RPGEngine.sync_character_stats(other, len(combat_state.combat_party))

            # Trigger death checks on target
            cls.check_and_trigger_death(target, combat_state, logs)

        # Sync stats
        RPGEngine.sync_character_stats(target, len(combat_state.combat_party))
"""

content = content[:start_idx] + new_code + content[end_idx:]

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Modification successful!")
