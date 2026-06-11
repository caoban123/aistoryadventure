from __future__ import annotations
import json
from time import perf_counter
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.auth.firebase_auth import get_current_user
from app.domain.rpg_schemas import (
    RPGStartRequest, RPGTurnRequest, RPGPromptTurnRequest,
    RPGEventActionRequest, RPGCombatActionRequest,
    RPGShopBuyRequest, RPGShopBuyMercRequest, RPGShopSellRequest,
    RPGPartySwapRequest, RPGEquipRequest,
    RPGQuestRefreshRequest, RPGFastTravelRequest, RPGLeaveRegionRequest,
    RPGTurnResponse, RPGCombatResponse, RPGShopResponse
)
from app.services.rpg_service import RPGService
from app.api.story_routes import (
    enforce_player_or_http,
    ensure_points_or_http,
    spend_points_or_http,
    ensure_rate_limit_or_http,
    log_ai_flow,
    estimate_token_count,
    request_token_estimate
)

router = APIRouter(prefix="/game/rpg", tags=["RPG"])
service = RPGService()

def response_token_estimate(value: dict | str) -> int:
    text = str(value)
    return estimate_token_count(text)

# --- Khởi tạo game ---

@router.post("/start")
async def start_rpg_game(
    request: RPGStartRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        result = await service.start_rpg_game(request, user_id=user["uid"])
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/roll-gold")
async def roll_gold(
    session_id: str,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.roll_gold(session_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/roll-equipment")
async def roll_equipment(
    session_id: str,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.roll_equipment(session_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/start-story", response_model=RPGTurnResponse)
async def start_story(
    session_id: str,
    region: str | None = None,
    objective: str | None = None,
    appearance_desc: str | None = None,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    # Start story makes an AI narrative call: costs points & rate limits
    estimated_input_tokens = estimate_token_count(session_id)
    await ensure_rate_limit_or_http(user, "start_adventure", "rpg.start_story", estimated_input_tokens)
    await ensure_points_or_http(user, "start_adventure")
    started_at = perf_counter()
    
    try:
        result = await service.start_rpg_story(
            session_id,
            user_id=user["uid"],
            region=region,
            objective=objective,
            appearance_desc=appearance_desc
        )
        points_entry = await spend_points_or_http(user, "start_adventure", session_id)
        await log_ai_flow(
            user=user,
            action="start_adventure",
            operation="rpg.start_story",
            status="success",
            started_at=started_at,
            session_id=session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0
        )
        return result
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="start_adventure",
            operation="rpg.start_story",
            status="error",
            started_at=started_at,
            session_id=session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.get("/suggest-names")
async def suggest_names(
    gender: str = "Male",
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.suggest_names(gender, user_id=user["uid"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.get("/suggest-objectives")
async def suggest_objectives(
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.suggest_objectives(user_id=user["uid"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

# --- Main Turn ---

@router.post("/turn", response_model=RPGTurnResponse)
async def process_turn(
    request: RPGTurnRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(user, "turn", "rpg.turn", estimated_input_tokens)
    await ensure_points_or_http(user, "turn")
    started_at = perf_counter()
    
    try:
        result = await service.process_turn(request.session_id, request.choice_index, user_id=user["uid"], background_tasks=background_tasks)
        points_entry = await spend_points_or_http(user, "turn", request.session_id)
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.turn",
            status="success",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0
        )
        return result
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.turn",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/turn/prompt", response_model=RPGTurnResponse)
async def process_turn_prompt(
    request: RPGPromptTurnRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(user, "turn", "rpg.turn_prompt", estimated_input_tokens)
    await ensure_points_or_http(user, "turn")
    started_at = perf_counter()
    
    try:
        result = await service.process_turn_prompt(request.session_id, request.player_input, user_id=user["uid"], background_tasks=background_tasks)
        points_entry = await spend_points_or_http(user, "turn", request.session_id)
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.turn_prompt",
            status="success",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0
        )
        return result
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.turn_prompt",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

# --- Monk, Merchant, Stranger, Item Events ---

@router.post("/event/monk/action", response_model=RPGTurnResponse)
async def process_monk_action(
    request: RPGEventActionRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    # Monk action requires AI narrative -> check rate limit and points
    await ensure_rate_limit_or_http(user, "turn", "rpg.event_monk", estimated_input_tokens)
    await ensure_points_or_http(user, "turn")
    started_at = perf_counter()
    
    try:
        result = await service.process_monk_action(request.session_id, request.action, user_id=user["uid"])
        points_entry = await spend_points_or_http(user, "turn", request.session_id)
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.event_monk",
            status="success",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0
        )
        return result
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.event_monk",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/event/merchant/action", response_model=RPGTurnResponse)
async def process_merchant_action(
    request: RPGEventActionRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(user, "turn", "rpg.event_merchant", estimated_input_tokens)
    await ensure_points_or_http(user, "turn")
    started_at = perf_counter()
    
    try:
        result = await service.process_merchant_action(request.session_id, request.action, user_id=user["uid"])
        points_entry = await spend_points_or_http(user, "turn", request.session_id)
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.event_merchant",
            status="success",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0
        )
        return result
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.event_merchant",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/event/stranger/action")
async def process_stranger_action(
    request: RPGEventActionRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(user, "turn", "rpg.event_stranger", estimated_input_tokens)
    await ensure_points_or_http(user, "turn")
    started_at = perf_counter()
    
    try:
        result = await service.process_stranger_action(request.session_id, request.action, user_id=user["uid"])
        points_entry = await spend_points_or_http(user, "turn", request.session_id)
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.event_stranger",
            status="success",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0
        )
        return result
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.event_stranger",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/event/item/action", response_model=RPGTurnResponse)
async def process_item_action(
    request: RPGEventActionRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(user, "turn", "rpg.event_item", estimated_input_tokens)
    await ensure_points_or_http(user, "turn")
    started_at = perf_counter()
    
    try:
        result = await service.process_item_action(request.session_id, request.action, user_id=user["uid"])
        points_entry = await spend_points_or_http(user, "turn", request.session_id)
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.event_item",
            status="success",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0
        )
        return result
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.event_item",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

# --- Combat ---

@router.post("/combat/action", response_model=RPGCombatResponse)
async def process_combat_action(
    request: RPGCombatActionRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    # Combat processes deterministic calculations + AI round narrative.
    # To prevent points drainage during lengthy fights, we log the AI flow but charge 0 points (combat actions are FREE of point cost)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(user, "turn", "rpg.combat_action", estimated_input_tokens)
    started_at = perf_counter()
    
    try:
        result = await service.process_combat_action(request.session_id, request, user_id=user["uid"])
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.combat_action",
            status="success",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=0
        )
        return result
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.combat_action",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/combat/end-action", response_model=RPGTurnResponse)
async def process_combat_end_action(
    request: RPGEventActionRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    estimated_input_tokens = request_token_estimate(request)
    await ensure_rate_limit_or_http(user, "turn", "rpg.combat_end", estimated_input_tokens)
    await ensure_points_or_http(user, "turn")
    started_at = perf_counter()
    
    try:
        result = await service.process_combat_end_action(request.session_id, request.action, user_id=user["uid"], custom_name=request.custom_name)
        points_entry = await spend_points_or_http(user, "turn", request.session_id)
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.combat_end",
            status="success",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0
        )
        return result
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.combat_end",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

# --- Shop ---

@router.post("/shop/refresh", response_model=RPGShopResponse)
async def shop_refresh(
    session_id: str,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.process_shop_refresh(session_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/shop/upgrade", response_model=RPGShopResponse)
async def shop_upgrade(
    session_id: str,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.process_shop_upgrade(session_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/shop/buy-item", response_model=RPGShopResponse)
async def shop_buy_item(
    request: RPGShopBuyRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.process_shop_buy_item(request.session_id, request.item_index, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/shop/buy-merc", response_model=RPGShopResponse)
async def shop_buy_merc(
    request: RPGShopBuyMercRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.process_shop_buy_merc(request.session_id, request.merc_index, user_id=user["uid"], custom_name=request.custom_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/shop/sell-item", response_model=RPGShopResponse)
async def shop_sell_item(
    request: RPGShopSellRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.process_shop_sell_item(request.session_id, request.item_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

# --- Party & Inventory ---

@router.post("/party/swap")
async def swap_party(
    request: RPGPartySwapRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.swap_party_members(request.session_id, request.from_position, request.to_position, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/party/equip")
async def equip_item(
    request: RPGEquipRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.equip_item(request.session_id, request.character_id, request.item_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/party/unequip")
async def unequip_item(
    session_id: str,
    character_id: str,
    slot: str,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.unequip_item(session_id, character_id, slot, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/inventory/use")
async def use_item(
    request: RPGEquipRequest,  # Reuse RPGEquipRequest (has session_id, character_id, item_id)
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.use_consume_item(request.session_id, request.character_id, request.item_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/quest/refresh")
async def refresh_quest(
    request: RPGQuestRefreshRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.refresh_quest(request.session_id, request.quest_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/fast-travel", response_model=RPGTurnResponse)
async def fast_travel(
    request: RPGFastTravelRequest,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    estimated_input_tokens = estimate_token_count(request.session_id) + estimate_token_count(request.target_region)
    await ensure_rate_limit_or_http(user, "turn", "rpg.fast_travel", estimated_input_tokens)
    await ensure_points_or_http(user, "turn")
    started_at = perf_counter()
    
    try:
        result = await service.fast_travel(request.session_id, request.target_region, user_id=user["uid"], background_tasks=background_tasks)
        points_entry = await spend_points_or_http(user, "turn", request.session_id)
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.fast_travel",
            status="success",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0
        )
        return result
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.fast_travel",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/leave-region", response_model=RPGTurnResponse)
async def leave_region(
    request: RPGLeaveRegionRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    estimated_input_tokens = estimate_token_count(request.session_id)
    await ensure_rate_limit_or_http(user, "turn", "rpg.leave_region", estimated_input_tokens)
    await ensure_points_or_http(user, "turn")
    started_at = perf_counter()
    
    try:
        result = await service.leave_region(request.session_id, user_id=user["uid"])
        points_entry = await spend_points_or_http(user, "turn", request.session_id)
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.leave_region",
            status="success",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=response_token_estimate(result),
            points_delta=points_entry.delta if points_entry else 0
        )
        return result
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await log_ai_flow(
            user=user,
            action="turn",
            operation="rpg.leave_region",
            status="error",
            started_at=started_at,
            session_id=request.session_id,
            estimated_input_tokens=estimated_input_tokens,
            error=exc
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

# --- State ---

@router.get("/state")
async def get_state(
    session_id: str,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.get_game_state(session_id, user_id=user["uid"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/session/restore")
async def restore_session(
    request: dict,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        session_id = request.get("session_id")
        game_state = request.get("game_state")
        if not session_id or not game_state:
            raise HTTPException(status_code=400, detail="Thiếu session_id hoặc game_state.")
        
        await service.restore_rpg_game(session_id, game_state, user_id=user["uid"])
        return {"success": True, "session_id": session_id}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/suggest-appearance")
async def suggest_appearance(
    player_name: str,
    gender: str,
    region: str,
    objective: str,
    gold: int,
    equipment_name: str,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.suggest_appearance(
            player_name=player_name,
            gender=gender,
            region=region,
            objective=objective,
            gold=gold,
            equipment_name=equipment_name,
            user_id=user["uid"]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/image/see-world")
async def see_world_image(
    session_id: str,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.generate_world_image(session_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@router.post("/image/refresh-character")
async def refresh_character_image(
    session_id: str,
    character_id: str,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.refresh_character_image(session_id, character_id, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

from pydantic import BaseModel

class RPGDebugCommandRequest(BaseModel):
    session_id: str
    command: str

@router.post("/debug/command")
async def run_debug_command(
    request: RPGDebugCommandRequest,
    user=Depends(get_current_user)
):
    await enforce_player_or_http(user)
    try:
        return await service.execute_debug_command(request.session_id, request.command, user_id=user["uid"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
