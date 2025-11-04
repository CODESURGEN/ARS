DEFAULT_QUERY = """
SELECT
    c.CustOrderNumber as 'Order Number',
    c.OrderedDate as 'Purchased on',
    c.TotalAmount as 'Total Purchased',
    c.Subtotal as 'Subtotal Purchased',
    c.TaxAmount as 'Tax',
    c.ShippingCharge as 'Shipping',
    c.CouponValue as 'Discount',
    v.TotalAmount as 'Vendor Amount',
    v.Subtotal as 'Vendor Subtotal',
    v.ShippingCharges as 'Vendor Shipping',
    CASE v.VendorID
        WHEN 1 THEN 'AllPoints'
        WHEN 2 THEN 'ReliableParts'
        WHEN 3 THEN 'Neuco'
        WHEN 4 THEN 'Metropac'
        WHEN 5 THEN 'Encompass'
        WHEN 6 THEN 'UED'
        WHEN 7 THEN 'DLWholesale'
        ELSE 'Unknown'
    END as 'Vendor Name',
    c.PaymentMethod as 'Payment Method',
    c.PaymentTransId as 'Payment Transaction ID'
    c.Return
FROM
    CustOrderDetails AS c
INNER JOIN
    VendorOrders AS v
ON
    c.CustOrderNumber = v.PONumber
WHERE
    c.OrderedDate >= '2025-07-01'
ORDER BY
    c.OrderedDate DESC;
"""


