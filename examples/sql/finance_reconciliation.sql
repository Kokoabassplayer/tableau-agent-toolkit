-- Finance Reconciliation Query
-- Compares GL balances with subledger balances for reconciliation
SELECT
    gl.account_number,
    gl.account_name,
    gl.balance AS gl_balance,
    sl.balance AS subledger_balance,
    gl.balance - sl.balance AS variance_amount,
    CASE
        WHEN gl.balance = 0 THEN NULL
        ELSE ABS(gl.balance - sl.balance) / ABS(gl.balance)
    END AS variance_pct,
    gl.period,
    gl.fiscal_year
FROM general_ledger gl
FULL OUTER JOIN subledger sl
    ON gl.account_number = sl.account_number
    AND gl.period = sl.period
    AND gl.fiscal_year = sl.fiscal_year
WHERE gl.period = DATE_TRUNC('month', CURRENT_DATE)
ORDER BY ABS(gl.balance - sl.balance) DESC;
