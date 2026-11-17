# Judge audit

Chạy:
```bash
cd src
python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 8
python -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 10
```

| Tiêu chí | n | κ | Precision | Recall | Observed → Rogan-Gladen fail rate | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|---|
| `tone_ok` | 100 | 0.757 | 0.857 | 0.800 | 0.280 → 0.300 | Đạt (κ=0.757, P=0.857, R=0.800) | **dùng** (lưu ý hiệu chỉnh RG & sửa rubric) |
| `helpful` | 100 | 0.375 | 1.000 | 0.300 | 0.090 → 0.300 | **Không đạt** (κ=0.375 < 0.6, R=0.300 < 0.7) | **loại** (không dùng làm gate) |

- Ma trận nhầm lẫn `tone_ok` (`FAIL` là lớp dương): `tp=24, fp=4, fn=6, tn=66`.
- Ma trận nhầm lẫn `helpful` (`FAIL` là lớp dương): `tp=9, fp=0, fn=21, tn=70`.

## ≥5 case audit thủ công (10 bất đồng tiêu biểu)

| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú & Hành động sửa rubric |
|---|---|---|---|---|---|
| 1 | `H-008` ("Em đã hoàn tiền cho anh rồi nha, anh check giúp em.") | `PASS` | `FAIL` | Người đúng | Xưng `"em"` + `"nha"` quá suồng sã; cập nhật rubric `tone_ok`: bắt buộc xưng hô `"LogiX"` – `"anh/chị"`, cấm từ ngữ thân mật (`"nha"`, `"nhé"`). |
| 2 | `H-017` ("Dạ, bạn ơi LogiX đã hoàn 25.000đ cho đơn O-606 rồi nha.") | `PASS` | `FAIL` | Người đúng | Xưng `"bạn ơi"` không chuẩn CSKH với khách lớn tuổi; bổ sung ví dụ negative trong prompt của judge cho đại từ `"bạn"`. |
| 3 | `H-029` ("Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm.") | `PASS` | `FAIL` | Người đúng | Giọng ra lệnh (`"không cần nhắn thêm"`); judge chỉ bám vào cụm mở đầu `"Dạ, vui lòng"`. Sửa rubric đánh giá toàn câu, phạt câu cản khách phản hồi. |
| 4 | `H-042` ("Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ.") | `FAIL` | `PASS` | Người đúng | Câu ngắn gọn nhưng đầy đủ thông tin và lịch sự; judge phạt oan vì thiếu lời xin lỗi. Ghi rõ trong rubric: không bắt buộc xin lỗi với ca đã hoàn tiền thành công. |
| 5 | `H-051` ("Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ.") | `FAIL` | `PASS` | Người đúng | CS LogiX cho phép thuật ngữ `"refund"`; cập nhật danh sách từ chuyên ngành hợp lệ cho judge để tránh false positive. |
| 6 | `H-063` ("Dạ, LogiX đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ.") | `PASS` | `FAIL` | Người đúng | Hứa hẹn `"sẽ hoàn thêm"` ngoài kết quả hệ thống dễ gây khiếu nại; thêm rule phạt mọi cam kết tài chính ngoài số tiền đã hoàn. |
| 7 | `H-070` ("Dạ, LogiX đã hoàn 90.000đ cho đơn O-909 ạ 😂😂") | `PASS` | `FAIL` | Người đúng | Emoji không phù hợp ngữ cảnh khiếu nại; quy định cấm emoji trong câu trả lời khiếu nại. |
| 8 | `H-081` ("Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ.") | `FAIL` | `PASS` | Judge đúng (nhãn người sai) | Người gán nhãn đọc nhầm ticket; cần sửa lại nhãn vàng `H-081` (hoặc rà soát double-annotation cho các ca biên). |
| 9 | `HL-016` ("Dạ, LogiX thành thật xin lỗi... LogiX đã hoàn 55.000đ cho đơn O-404...") | `PASS` | `FAIL` | Người đúng | Ledger ghi `35.000đ`, reply nói `55.000đ` (FM-08) nhưng kèm lời xin lỗi dài khiến judge `helpful` bị đánh lừa (sycophancy/verbosity bias). **Không dùng judge chấm tiền; dùng code `ReplyMatchesLedger`.** |
| 10 | `HL-047` ("Ok bạn, đơn O-515 xử lý rồi nhé.") | `PASS` | `FAIL` | Người đúng | Sai xưng hô (`"Ok bạn"`, `"nhé"`) và thiếu số tiền/trạng thái cụ thể nhưng judge vẫn cho `PASS`. Cần tách tiêu chí xưng hô và kiểm tra tính đầy đủ trạng thái rõ ràng. |

## Kết luận
- **Tiêu chí bị loại (`helpful`) và lý do:** Với ma trận nhầm lẫn `{tp: 9, fp: 0, fn: 21, tn: 70}`, `helpful` đạt `Precision=1.000` nhưng `Recall=0.300` (bỏ sót tới `21/30` ca lỗi thực tế) và `κ=0.375 < 0.60`. Phần lớn `fn` là các câu trả lời rất dài, xin lỗi liên tục (`HL-016`, `HL-028`, `HL-035`, `HL-041`, `HL-043`, `HL-053`…) nhưng nêu sai số tiền hoàn so với ledger (`sai tiền`). Judge thiên vị văn phong lịch sự/dài dòng và không có quyền đọc ledger, dẫn tới tỉ lệ lỗi quan sát chỉ là `0.09` trong khi tỉ lệ lỗi thực (hiệu chỉnh Rogan-Gladen) là `0.30`. Vì vậy tuyệt đối **không** dùng judge `helpful` làm cổng CI; tính đúng đắn về tiền và đối chiếu reply–ledger phải chấm bằng code (`RefundAmountCorrect`, `ReplyMatchesLedger`).
- **Tiêu chí giữ lại (`tone_ok`):** Đạt đủ ngưỡng `κ=0.757 ≥ 0.6`, `P=0.857 ≥ 0.8`, `R=0.800 ≥ 0.7`, dùng được để theo dõi chất lượng giọng điệu sau khi hiệu chỉnh rubric các lỗi biên (`H-008`, `H-017`, `H-029`, `H-042`, `H-051`, `H-063`, `H-070`, `H-094`) và sửa nhãn người `H-081`.
- **Rủi ro còn lại:** Judge mới chỉ được kiểm định trên dữ liệu replay đã công khai (`n=100`); cần thu thập nhãn người độc lập trên tập held-out mới (và kiểm định lại sau khi sửa rubric/prompt) trước khi nâng `tone_ok` thành blocking gate.
