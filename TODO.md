# TODO - Supervisor Grade Selection on Dissertation Approval

## Step 1: Inspect current supervisor/dissertation approval flow
- [x] Read backend/app.py to locate supervisor defence endpoint and current grade handling.
- [x] Read frontend pages; no supervisor-specific UI found in the provided frontend/pages (office-dashboard.html only contains office clearance + document review modals).

## Step 2: Backend validation (enforce grade required only when passed)
- [x] Update /api/supervisor/defense/<student_id> so that when status='passed' the API blocks submission if grade is missing, returning exactly: "Please select a dissertation grade before approving.".

## Step 3: Persist selected grade
- [x] Confirm the endpoint already saves dissertation_grade into student_profiles for status='passed'.

## Step 4: Link to Graduating Students List
- [x] Confirm /api/clearance/final-graduating-students already selects sp.dissertation_grade and displays it in office-dashboard.html.

## Step 5: Frontend UI change (dropdown/radio + client-side validation)
- [ ] Add/locate the supervisor approval modal/page and update it with a required "Dissertation Grade" selector.
- [ ] Ensure approve action sends {status:'passed', grade:<selected>} to /api/supervisor/defense/<student_id>.

## Step 6: Testing
- [ ] Run test_approval_flow.py or similar if available, and add a minimal test for missing grade when status='passed'.

