import re

class SafetyFilterService:
    def __init__(self) -> None:
        # Predefined categories of banned patterns (Vietnamese and English)
        self.categories = {
            "violence": [
                r"(giết người|thảm sát|tự tử|tự sát|suicide|kill|murder|torture|tra tấn|máu me|chặt đầu|decapitate|self-harm|cắt cổ|đâm chết)",
            ],
            "adult": [
                r"(sex|porn|đồi trụy|hiếp dâm|cưỡng bức|rape|nsfw|khỏa thân|nude|hãm hiếp|dâm ô|thủ dâm|masturbate|phim người lớn)",
            ],
            "vulgarity": [
                r"\b(đm|đkm|vcl|đéo|fuck|asshole|bitch|slut|ngu lờ|đầu buồi|hãm lồn|cặc|lồn|buồi|đút đít|mẹ kiếp|chó đẻ|dcm|đm)\b"
            ]
        }
        
        # Compile patterns for fast matching
        self.compiled_patterns = {}
        for category, patterns in self.categories.items():
            combined = "|".join(patterns)
            self.compiled_patterns[category] = re.compile(combined, re.IGNORECASE)

    def validate_input(self, text: str, field_name: str = "Dữ liệu đầu vào") -> None:
        """
        Validates if the text is safe. Raises ValueError if unsafe content is detected.
        """
        if not text:
            return

        for category, pattern in self.compiled_patterns.items():
            if pattern.search(text):
                if category == "violence":
                    raise ValueError(f"{field_name} chứa nội dung bạo lực hoặc tự hại không phù hợp.")
                elif category == "adult":
                    raise ValueError(f"{field_name} chứa nội dung nhạy cảm hoặc người lớn không được phép.")
                else:
                    raise ValueError(f"{field_name} chứa từ ngữ thô tục hoặc không phù hợp quy chuẩn ứng xử.")

    def censor_output(self, text: str) -> str:
        """
        Censors unsafe words in the text, replacing them with a warning placeholder.
        """
        if not text:
            return text

        censored_text = text
        for category, pattern in self.compiled_patterns.items():
            # Replace all occurrences of matching patterns with a placeholder
            censored_text = pattern.sub("[Nội dung đã được lược bỏ để đảm bảo an toàn]", censored_text)
            
        return censored_text
