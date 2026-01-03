
-- =============================================
-- VALIDIERUNG: Kampagnen-Umsatz mit ROAS
-- =============================================

-- Query wie im Dashboard verwendet (mit Kosten und ROAS)
-- Kosten werden über ID_CAMPAIGN gejoint (extrahiert aus "Marketing Campaign [ID]: Name")
WITH KampagnenUmsatz AS (
    SELECT
        s.ID_STORE,
        so.STORE_LOCATION AS StoreName,
        c.ID_CAMPAIGN,
        c.CAMP_TYPE + ': ' + c.CAMP_NAME AS Kampagne,
        SUM(s.RevenueEUR) AS Umsatz
    FROM dbo.V_LIST_MONTHLY_SALES s
    INNER JOIN dbo.T_CAMPAIGN c ON s.ID_CAMPAIGN = c.ID_CAMPAIGN
    INNER JOIN dbo.T_SALESORG so ON s.ID_STORE = so.SALESORG_ID
    WHERE s.ID_STORE IN (3, 5, 14)
    AND s.ID_CAMPAIGN != 0
    GROUP BY s.ID_STORE, so.STORE_LOCATION, c.ID_CAMPAIGN, c.CAMP_TYPE, c.CAMP_NAME
),
KampagnenKosten AS (
    -- Kosten aus V_LIST_MONTHLY_COSTS
    -- Format: "Marketing Campaign [ID]: Name" -> extrahiere ID
    SELECT
        ID_STORE,
        CAST(SUBSTRING(
            Kostenkategorie,
            CHARINDEX('[', Kostenkategorie) + 1,
            CHARINDEX(']', Kostenkategorie) - CHARINDEX('[', Kostenkategorie) - 1
        ) AS INT) AS ID_CAMPAIGN,
        SUM(WertEUR) AS Kosten
    FROM dbo.V_LIST_MONTHLY_COSTS
    WHERE Kostenkategorie LIKE 'Marketing Campaign [%'
    AND ID_STORE IN (3, 5, 14)
    GROUP BY ID_STORE, CAST(SUBSTRING(
        Kostenkategorie,
        CHARINDEX('[', Kostenkategorie) + 1,
        CHARINDEX(']', Kostenkategorie) - CHARINDEX('[', Kostenkategorie) - 1
    ) AS INT)
),
StoreGesamt AS (
    SELECT
        ID_STORE,
        SUM(Umsatz) AS GesamtUmsatz
    FROM KampagnenUmsatz
    GROUP BY ID_STORE
)
SELECT
    k.StoreName,
    k.Kampagne,
    k.Umsatz,
    ISNULL(kk.Kosten, 0) AS Kosten,
    g.GesamtUmsatz AS StoreGesamtUmsatz,
    CAST(k.Umsatz * 100.0 / g.GesamtUmsatz AS DECIMAL(10,2)) AS AnteilProzent,
    CASE
        WHEN ISNULL(kk.Kosten, 0) > 0 THEN CAST(k.Umsatz / kk.Kosten AS DECIMAL(10,2))
        ELSE NULL
    END AS ROAS
FROM KampagnenUmsatz k
INNER JOIN StoreGesamt g ON k.ID_STORE = g.ID_STORE
LEFT JOIN KampagnenKosten kk ON k.ID_STORE = kk.ID_STORE AND k.ID_CAMPAIGN = kk.ID_CAMPAIGN
ORDER BY k.ID_STORE, k.Umsatz DESC;

