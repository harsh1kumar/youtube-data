---------------------------------------------------------
-- Retain only unique records for every run
---------------------------------------------------------

-- CREATE OR REPLACE TABLE `wide-hexagon-397214.youtube_data.channel_info` AS
WITH max_timestamp AS (
    SELECT 
        DATE(load_timestamp) AS dt,
        MAX(load_timestamp) AS max_load_timestamp
    FROM `wide-hexagon-397214.youtube_data.channel_info`
    GROUP BY 1
    ORDER BY 1
)

SELECT
    channel.*
FROM `wide-hexagon-397214.youtube_data.channel_info` AS channel
INNER JOIN max_timestamp AS max_t
ON channel.load_timestamp=max_t.max_load_timestamp
ORDER BY load_timestamp, channel_name
;


