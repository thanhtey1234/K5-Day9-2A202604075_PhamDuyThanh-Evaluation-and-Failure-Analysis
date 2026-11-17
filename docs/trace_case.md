# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (case C-002@11 từ report v1)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, report run ID `E-seeded_regression-20261118-7976` (trace run ID `R-seeded_regression-C-002-s11`) |
| Triệu chứng | `TrialPass` (`pass_rate`), `DbFactKept` (`db_fact_kept`), `RefundAmountCorrect` (`refund_amount_correct`), `ProposalMatchesQuote` (`proposal_matches_quote`) đều fail (`status resolved != denied`): ledger ghi `refund_vnd=20000`, `refund_count=1` (nhãn `0`), `result.status=resolved` (nhãn `denied`), event 6 `reply` nói `"Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."` |
| Bước sai đầu tiên | Event `3` `model_override` — `{"delay_days": 5}` |
| Vì sao là bước *đầu tiên* | Event `1` `handoff` đúng hợp đồng `handoff.v1` (allowlist 3 tool chỉ đọc, không lộ secret); Event `2` `investigator` (`lookup_order`) đã đọc đúng dữ liệu DB (`"order_id": "O-202", "status": "delivered", "delay_days": 2, "shipping_fee_vnd": 20000`). Tới Event `3`, shape tin cụm `"trễ 5 ngày"` trong ticket để ghi đè `delay_days` từ `2` thành `5`, kéo theo Event `4` `quote` tính sai `20000` và ghi nhầm hoàn tiền vào ledger. |
| Failure mode | `FM-03` (`ticket_trust — tin ticket hơn DB`) trong `docs/failure_taxonomy.md` |
| Đối chứng | Cùng `C-002@11` trên shape `fixed` (trace `R-fixed-C-002-s11`): sau Event `1` `handoff` và Event `2` `investigator` (`delay_days=2`), không có event `model_override`; Event `3` là `quote {"amount_vnd": 0, "reason": "no_entitlement", "clause_ids": [], "parts": {}}`, Event `4` `reply` từ chối lịch sự, ledger `refund_vnd=0`, `refund_count=0`, `status=denied` (PASS). |
| Regression test | `test_trace_case_c002_seed11_ticket_override_caught_and_fixed` trong [test_lab9_regression.py](file:///c:/Users/DUY%20THANH%20PHAM/K5-Day9-2A202604075_PhamDuyThanh-Evaluation-and-Failure-Analysis/src/tests/test_lab9_regression.py) — assert `TrialPass`, `DbFactKept`, `RefundAmountCorrect` đều `False` trên `seeded_regression C-002@11` và đều `True` trên `fixed C-002@11` (đã xác nhận xanh khi chạy `python -m pytest -q -m student -o addopts= -k "lab9 and not advanced"`). |
| Chưa chắc chắn | Trace hiện tại chỉ chứng minh lỗi khi shape ghi event `model_override`; nếu một biến thể ẩn tin ticket nhưng bỏ qua việc ghi `model_override` (như `quiet_override`), `DbFactKept` (step-level) sẽ không phát hiện được mà phải dựa vào outcome-level (`TrialPass`, `RefundAmountCorrect`) và slice gate (`denial`, `adversarial`). |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: đã thêm vào `src/tests/test_lab9_regression.py`.
