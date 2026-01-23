# Project Documentation & Code Flow

This document provides a comprehensive overview of the entire project, breaking down every major feature, its corresponding code files, and the logic behind it.

## System Overview Table

| Feature / Page | File(s) Involved | User Action | System Logic (Behind the Scenes) |
| :--- | :--- | :--- | :--- |
| **Landing Page** | `views.py` (home)<br>`urls.py` | Opens Website | Checks if user is logged in.<br>• **If Logged In:** Redirects to appropriate Dashboard (User/Admin/Conductor).<br>• **If Guest:** Shows Login Page. |
| **User Registration** | `views.py` (register)<br>`forms.py` (CustomUserCreationForm) | Fills Sign Up Form | Validates password match & username uniqueness.<br>Creates new `CustomUser` with role='USER'.<br>Redirects to Login page. |
| **Login** | `views.py` (custom_login)<br>`forms.py` (AuthenticationForm) | Enters Credentials | Verifies username/password.<br>Checks Role.<br>• **Admin/Conductor:** Blocked (must use restricted portal).<br>• **User:** Logged in & redirected to User Dashboard. |
| **Google Login** | `views.py` (google_login, google_callback) | Clicks "Login with Google" | Redirects to Google OAuth.<br>On callback, checking if email exists.<br>• **Exists:** Logs in user.<br>• **New:** Creates account automatically & logs in. |
| **User Dashboard** | `views.py` (user_dashboard)<br>`templates/user_dashboard.html` | Views Dashboard | Fetches Wallet Balance, Active Tickets, Payment History.<br>Checks for expired passes/tickets.<br>Renders QR Codes (if valid). |
| **Searching Buses** | `views.py` (user_dashboard template logic) | Selects From/To Cities | JavaScript filters available Routes based on selection.<br>Displays list of buses with costs and timings. |
| **Buying Ticket** | `views.py` (buy_ticket)<br>`models.py` (Ticket, Payment) | Clicks "Purchase Ticket" | Checks Wallet Balance (`>= Cost`).<br>• **Yes:** Deducts amount, Creates `Ticket`, Records `Payment`, Generating QR Code.<br>• **No:** Shows "Insufficient Balance" error. |
| **Refilling Wallet** | `views.py` (recharge_wallet)<br>`payment_page` | Clicks "Add 100" | **Payment Page:** Initiates Razorpay order.<br>**Success:** Updates `CustomUser.balance`, Records `Payment` (Type: REFILL). |
| **Ticket Details (Modal)** | `views.py` (render_barcode_image)<br>`templates/user_dashboard.html` | Clicks "View Details" | Opens modal with full ticket info.<br>Fetches dynamic QR Code image via `/barcode/<code>/` URL. |
| **Download Ticket** | `views.py` (download_ticket_ppt) | Clicks "Download PPT" | Generates a PowerPoint (.pptx) file.<br>Embeds Trip Details and QR Code image into the slide.<br>Triggers file download. |
| **Conductor Login** | `views.py` (conductor_login) | Staff logs in | Dedicated portal for Staff.<br>Blocks standard Users.<br>Redirects to Admin or Conductor Dashboard. |
| **Conductor Dashboard** | `views.py` (conductor_dashboard)<br>`templates/conductor_dashboard.html` | Staff View | Simple interface for scanning tickets. |
| **Verifying Ticket** | `views.py` (validate_ticket, conductor_dashboard) | Scans/Enters Barcode | Searches `Ticket` or `Pass` by unique barcode string.<br>Checks:<br>1. Exist?<br>2. Expired? (`> 10 mins` after departure)<br>3. Already Used?<br>Returns **Valid** (Green) or **Invalid** (Red). |
| **Admin Dashboard** | `views.py` (admin_dashboard)<br>`templates/admin_dashboard.html` | Admin View | Shows System Stats (Total Users, Revenue).<br>Lists Conductors.<br>Tools to Add/Delete Cities and Routes. |
| **Manage Routes** | `views.py` (add_route, delete_route) | Admin adds Route | Creates new `Route` entry linking Source to Destination with Cost and Schedule. |
| **Manage Cities** | `views.py` (add_city, delete_city) | Admin adds City | Adds new location to the database for use in Routes. |

## Key Database Models (`models.py`)

| Model | Description |
| :--- | :--- |
| **CustomUser** | Extends default user. Adds `role` (Admin/User/Conductor) and `balance` (Wallet). |
| **City** | Represents a location (Name, State). |
| **Route** | Connects two Cities. Contains `cost`, `bus_number`, `gate`, `date`, `time`. |
| **Pass** | (Legacy) Represents a Monthly Pass. Has `valid_until` date and `barcode_data`. |
| **Ticket** | Represents a single trip purchase. Linked to User and Route. Validates via `is_expired` logic. |
| **Payment** | Ledger of all financial moves. Tracks Refills (`+`) and Purchases (`-`). |
