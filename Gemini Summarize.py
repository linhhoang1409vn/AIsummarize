import requests
import json
import os
import time

# Đọc API key từ file
api_key_path = r"D:\Code\API KEY\Gemini API Key.txt"
with open(api_key_path, "r", encoding="utf-8") as key_file:
    api_key = key_file.read().strip()

# Thư mục chứa file txt cần đọc
input_dir = r"D:\1\txt input"

# Thư mục lưu file tóm tắt
output_dir = r"D:\1\txt output summaries"

# Hàm khởi tạo URL API cho từng model
def get_api_url(key, model_version):
    if model_version == "2.5":
        return f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    else:
        raise ValueError("Model version không hợp lệ")

# Danh sách URL luân phiên theo model version
model_versions = ["2.5", "2.5"]
current_model_index = 0

# Khởi tạo URL ban đầu
url = get_api_url(api_key, model_versions[current_model_index])

# Header
headers = {
    "Content-Type": "application/json"
}

# Hàm lấy tất cả file .txt trong thư mục và subfolder
def get_all_txt_files(root_dir):
    txt_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.lower().endswith(".txt"):
                full_path = os.path.join(dirpath, filename)
                # Lấy đường dẫn thư mục con so với input_dir
                relative_dir = os.path.relpath(dirpath, root_dir)
                txt_files.append((full_path, relative_dir))
    return txt_files

file_list = get_all_txt_files(input_dir)

summary_count = 0
max_summaries_per_chat = 1

for file_path, relative_dir in file_list:
    # Đọc nội dung file txt
    with open(file_path, "r", encoding="utf-8") as f:
        text_content = f.read()

    # Đếm số chữ trong nội dung gốc
    original_word_count = len(text_content.split())

    # Payload dữ liệu gửi đi: yêu cầu tóm tắt chi tiết nội dung bằng tiếng Việt
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Tóm tắt nội dung sau bằng tiếng Việt, chỉ trả về phần tóm tắt chi tiết trên 1500 chữ hoặc một nửa nội dung cung cấp, không thêm lời giới thiệu hay nhận xét:\n\n{text_content}" 
                    }
                ]
            }
        ]
    }

    # Gửi POST request
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        summary_dict = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0]
        summary = summary_dict.get("text", "") if isinstance(summary_dict, dict) else summary_dict
        summary_clean = summary.replace("*", "").replace("#", "").strip()

        # Đếm số chữ trong nội dung tóm tắt
        summary_word_count = len(summary_clean.split())

        print(f"File: {os.path.basename(file_path)}")
        print(f"Bài gốc: {original_word_count} chữ")
        print(f"Bài tóm tắt: {summary_word_count} chữ")
        print(f"Nội dung tóm tắt:\n{' '.join(summary_clean.split()[:100])}\n")

        # Tạo thư mục output tương ứng với thư mục con của file nguồn
        output_subdir = os.path.join(output_dir, relative_dir)
        os.makedirs(output_subdir, exist_ok=True)

        # Tạo tên file output với tiền tố là tên file nguồn
        output_filename = f"{os.path.splitext(os.path.basename(file_path))[0]}_summary.txt"
        output_file_path = os.path.join(output_subdir, output_filename)

        # Ghi tóm tắt đã làm sạch ra file txt
        with open(output_file_path, "w", encoding="utf-8") as f_out:
            f_out.write(summary_clean)

        summary_count += 1

        # Sau 3 lần tóm tắt, đổi sang URL API tiếp theo trong danh sách model_versions
        if summary_count >= max_summaries_per_chat:
            current_model_index = (current_model_index + 1) % len(model_versions)
            url = get_api_url(api_key, model_versions[current_model_index])
            summary_count = 0  # reset bộ đếm

    else:
        print(f"Error for file {os.path.basename(file_path)}: {response.status_code}")
        print(response.text)

    # Chờ 1 giây trước khi xử lý file tiếp theo
    time.sleep(1)
