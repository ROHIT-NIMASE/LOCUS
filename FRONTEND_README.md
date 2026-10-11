# LOCUS - Frontend (CustomTkinter)

## Run
    pip install -r requirements.txt
    python main.py          # run from the project root
Demo login (mock data): `student` / `locus123`

## How the frontend is organised
    main.py                    one window; show_screen("name") switches screens
    theme.py                   colours + fonts (change the look here only)
    ui/                        one file per screen
    components/                reusable pieces (buttons, seat card, booking card, messages, header)
    services/backend.py        the single door the UI uses (just re-exports, no logic)
    services/user_service.py   register_user, login_user
    services/seat_service.py   get_seat_statuses, get_available_seat_count
    services/booking_service.py create/list/cancel booking, check_in, check_out
    services/responses.py      ok() / fail() helpers that build the return dictionary
    mock_data/data.py          dummy data used by the services for now (delete when MySQL is connected)

UI files never touch SQL or mock_data. They only call `services/backend.py`.

## For the backend teammates
Replace the BODY of each function in the three `*_service.py` files
(search for `# BACKEND INTEGRATION POINT`). Keep the names, inputs and return shape.
Do not edit `backend.py` or anything in `ui/`.

Every function returns a dictionary (use `ok()` / `fail()` from `services/responses.py`):
    {"success": True,  "message": "...", "data": ...}
    {"success": False, "message": "...", "data": None}     # the UI shows `message` to the student

| Function | File | Inputs | `data` on success |
|---|---|---|---|
| `register_user` | user_service | full_name, student_id, email, password | nothing needed |
| `login_user` | user_service | identifier (email OR username), password | user dict: user_id, full_name, student_id, email, username (no password) |
| `get_seat_statuses` | seat_service | booking_date, start_time, end_time | list of `{"seat_id": "A01", "status": "available"/"occupied"/"unavailable"}` |
| `get_available_seat_count` | seat_service | booking_date, start_time, end_time | integer |
| `create_booking` | booking_service | user_id, seat_id, booking_date, start_time, end_time | booking dict |
| `get_user_bookings` | booking_service | user_id | list of booking dicts (newest first) |
| `get_current_booking` | booking_service | user_id | the Active booking, else the soonest Upcoming one, else `None` |
| `cancel_booking` | booking_service | booking_id | updated booking dict |
| `check_in` | booking_service | booking_id | updated booking dict (status "Active") |
| `check_out` | booking_service | booking_id | updated booking dict (status "Completed") |

Booking dict: `booking_id, user_id, seat_id, date, start_time, end_time, status`

## Formats the UI expects
- date `"YYYY-MM-DD"`, time `"HH:MM"` (24-hour text)
- seat_id = one letter + two digits, e.g. `"A01"` (letter = row, number = column; the grid is drawn from these)
- booking status exactly one of: `Upcoming`, `Active`, `Completed`, `Cancelled`, `No-show`
- seat status exactly one of: `available`, `occupied`, `unavailable` ("selected" is UI-only)

## Things the backend decides (the UI does not)
- Real validation again (the UI only does basic checks), password hashing
- Booking limits, overlap rules, check-in time window, no-show handling
- `get_available_seat_count` is called by the dashboard with "now until one hour later",
  e.g. 06:11 - 07:11 (not only whole hours)
- `get_current_booking` feeds the Dashboard, Check-in and Check-out screens
- Opening hours (8:00-22:00) and the 7-day booking window are constants at the top of `ui/seats.py`

## When the real backend is connected
1. Delete the `mock_data/` folder (and its import in the service files)
2. Delete the "Demo login" label in `ui/login.py` (marked TEMPORARY)
