import json

path = r"d:\hcmus\HK4\Tư duy tính toán cho TTNT\aistoryadventure\gen-img.ipynb"
with open(path, "r", encoding="utf-8") as f:
    notebook = json.load(f)

new_source = """class UnifiedRequest(BaseModel):
    prompt: str
    world_name: str = "default_world"
    summarize_model: str # "gemini-2.5-flash" hoặc "Qwen/Qwen2.5-1.5B-Instruct"
    txt2img_model: str # "SDXL lightning" hoặc "Gemini API banana pro"
    step: int = 4

@app.post("/generate-world-theme")
async def generate_world_theme(request: UnifiedRequest):
    try:
        # Tự động phát hiện nếu prompt đã là tiếng Anh (không chứa các dấu thanh tiếng Việt)
        # để bỏ qua bước tóm tắt & dịch thuật nhằm giữ nguyên mô tả nhân vật tiếng Anh chi tiết.
        has_vietnamese = bool(re.search(
            r'[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệđìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]', 
            request.prompt, 
            re.IGNORECASE
        ))
        
        if not has_vietnamese:
            # Prompt đã bằng tiếng Anh, giữ nguyên
            en_prompt = request.prompt.strip()
        else:
            # Bước 1: Tóm tắt & Dịch thuật (cho các prompt tiếng Việt)
            if "gemini" in request.summarize_model.lower():
                en_prompt = await summarize_with_gemini(request.prompt)
            else:
                en_prompt = summarize_with_qwen(request.prompt)
        
        # Tự động nhận diện xem đây là ảnh chân dung (Avatar) hay cảnh thế giới (See the World)
        # dựa vào từ khóa trong prompt hoặc tên file đầu ra.
        is_portrait = any(
            k in en_prompt.lower() or k in request.world_name.lower() 
            for k in ["avatar", "portrait", "character", "monk", "merchant", "lemuen", "hoshiguma", "wang", "vinavictoria"]
        )
        
        if is_portrait:
            # Prompt phụ trợ chuyên cho vẽ chân dung nhân vật RPG
            final_prompt = f"{en_prompt}, close up portrait, headshot, character design, fantasy, masterpiece, highly detailed, cinematic lighting"
        else:
            # Prompt phụ trợ chuyên cho vẽ phong cảnh thế giới
            final_prompt = f"{en_prompt}, masterpiece, highly detailed, fantasy concept art, cinematic lighting"
            
        # Bước 2: Sinh hình ảnh
        if "sdxl" in request.txt2img_model.lower():
            image = pipe(final_prompt, num_inference_steps=request.step, guidance_scale=0).images[0]
        else:
            raise HTTPException(status_code=501, detail="Gemini Image API chưa được cấu hình cụ thể")

        # Bước 3: Lưu hình ảnh xuống Local (Kaggle Storage)
        save_dir = "generated_imgs/theme_stories"
        os.makedirs(save_dir, exist_ok=True)
        
        safe_name = sanitize_filename(request.world_name)
        file_path = os.path.join(save_dir, f"{safe_name}_theme.png")
        
        image.save(file_path) # Tự động ghi đè nếu trùng tên

        # Bước 4: Chuyển sang Base64 để trả về API
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return {
            "status": "success",
            "en_prompt": final_prompt,
            "saved_at": file_path,
            "image_base64": img_str
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))"""

# Sửa lại source của cell index 15. Trong notebook format, source nên là list các dòng
notebook["cells"][15]["source"] = [line + "\n" for line in new_source.split("\n")]

with open(path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)

print("Notebook updated successfully.")
