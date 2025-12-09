# Changelog

## 2025-11-30
- Pointed deploy script to production ECR account (906348407450) via `TARGET_AWS_ACCOUNT_ID` override for both API/UI images.
- Streamlit upgraded to 1.39.0 and rerun calls updated to `st.rerun()` to avoid SessionInfo bad message errors.
