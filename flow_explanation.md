# How the Bus Pass System Works (Simple Explanation)

This document explains what happens "behind the scenes" when you use the Bus Pass website. Think of the system as a smart digital assistant that listens to your clicks and follows a specific set of rules.

## 1. Opening the Website (Home Page)
**Action:** You open the website.

1.  **The Check:** The system first looks at your digital ID tag (session).
    *   **If you are NOT logged in:** It immediately shows you the **Login Page** so you can identify yourself.
    *   **If you ARE logged in:** It checks your "badge" (Role).
        *   If you have an **Admin Badge**: It sends you straight to the **Admin Dashboard** (the control center).
        *   If you have a **User Badge**: It sends you straight to the **User Dashboard** (your personal profile).

---

## 2. Registering a New Account
**Action:** You fill in your name and password and click "Sign Up".

1.  **The Review:** The system checks your form.
    *   Did you type the password correctly twice?
    *   Is that username already taken?
2.  **Creating the File:** If everything looks good, the system opens its big digital ledger (the database).
    *   It writes down your new username and password.
    *   It officially labels you as a regular **"User"** (not an Admin).
3.  **The Welcome:** The system automatically signs you in (gives you your ID tag) and sends you to your new **User Dashboard**.

---

## 3. Buying a Pass
**Action:** You click the "Buy Pass ($50)" button.

1.  **The Wallet Check:** The system looks at your digital wallet balance.
    *   **Is there at least $50?**
2.  **The Transaction (If you have enough money):**
    *   It takes $50 out of your wallet.
    *   It calculates a new date: **Today + 30 Days**.
    *   It stamps this new "Valid Until" date on your digital bus pass.
    *   It shows you a green "Success" message.
3.  **The Rejection (If you are broke):**
    *   It stops and shows you a red "Not enough money" error.
4.  **The Result:** The page refreshes. If you bought the pass, a **QR Code/Barcode** appears. This barcode represents your valid pass.

---

## 4. Refilling Your Wallet
**Action:** You type "100" and click "Refill".

1.  **The Math:** The system takes the number you typed (100).
2.  **The Update:** It finds your record in its ledger and adds 100 to your current balance number.
3.  **The Refresh:** It reloads the page. You now see your balance has gone up by 100.

---

## 5. Admin - Verifying a Pass
**Action:** The Conductor (Admin) scans or types a user's barcode number and clicks "Verify".

1.  **The Search:** The system looks through thousands of passes in its memory to find that specific barcode number.
2.  **The Judgment:**
    *   **If it finds nothing:** It says "Invalid Pass" (Fake!).
    *   **If it finds the pass:** It checks the date on it.
        *   Is the "Valid Until" date *in the future*? -> **"VALID PASS"** (Green Light).
        *   Is the "Valid Until" date *in the past*? -> **"EXPIRED PASS"** (Red Light).
3.  **The Report:** It shows the Conductor the result so they know whether to let the passenger on the bus.

---

## 6. Admin - Deleting a User
**Action:** The Admin clicks determining "Delete" next to a person's name.

1.  **The Find:** The system locates that specific person's file.
2.  **The Shredder:** It permanently erases that person's entire record (pass, balance, login info) from the digital ledger.
3.  **The Update:** The list of users reloads, and that person is gone.
