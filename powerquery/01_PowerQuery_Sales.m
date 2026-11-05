// =====================================================================
// Power Query (M) - cleans retail_sales_raw.csv into the "Sales" table
// HOW TO USE: Home > Get Data > Text/CSV > pick retail_sales_raw.csv > Transform Data.
// Then in the Power Query Editor: Home > Advanced Editor, delete everything,
// paste this whole script, change FilePath on line 12, click Done.
// Rename the query to "Sales".
// =====================================================================
let
    // ---- 0. Parameter: change this to where you saved the CSV --------
    FilePath = "C:\PowerBI_Project\retail_sales_raw.csv",

    // ---- 1. Load and promote headers ---------------------------------
    Source   = Csv.Document(File.Contents(FilePath), [Delimiter = ",", Columns = 15, Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),

    // ---- 2. Remove exact duplicate rows (550 in this file) -----------
    NoDuplicates = Table.Distinct(Promoted),

    // ---- 3. Trim spaces and fix capitalisation ----------------------
    ProperCols = {"CustomerSegment", "Region", "City", "Category", "SalesChannel", "PaymentMethod"},
    CleanText  = Table.TransformColumns(
                    NoDuplicates,
                    List.Transform(ProperCols, each {_, (v) => if v = null then null else Text.Proper(Text.Trim(v)), type nullable text})
                 ),
    TrimProduct = Table.TransformColumns(CleanText, {{"Product", each Text.Trim(_), type text}}),

    // ---- 4. Fix typos and brand capitalisation ----------------------
    FixTypo1 = Table.ReplaceValue(TrimProduct, "Electronis", "Electronics", Replacer.ReplaceValue, {"Category"}),
    FixTypo2 = Table.ReplaceValue(FixTypo1,    "Clothng",    "Clothing",    Replacer.ReplaceValue, {"Category"}),
    FixPayPal = Table.ReplaceValue(FixTypo2,   "Paypal",     "PayPal",      Replacer.ReplaceValue, {"PaymentMethod"}),

    // ---- 5. Replace missing text values with "Unknown" ---------------
    FillUnknown = Table.ReplaceValue(
                    FixPayPal, null, "Unknown", Replacer.ReplaceValue,
                    {"CustomerSegment", "City", "SalesChannel", "PaymentMethod"}
                  ),

    // ---- 6. Dates: three different formats, parsed as UK (day first) -
    FixDates = Table.TransformColumns(
                    FillUnknown,
                    {{"OrderDate", each Date.FromText(Text.Trim(_), [Culture = "en-GB"]), type date}}
               ),

    // ---- 7. UnitPrice: remove the pound sign / commas, make numeric -
    FixPrice = Table.TransformColumns(
                    FixDates,
                    {{"UnitPrice", each if _ = null or _ = "" then null
                                        else Number.FromText(Text.Replace(Text.Replace(_, "£", ""), ",", ""), "en-GB"),
                      type nullable number}}
               ),

    // ---- 8. Set data types for the other numeric columns ------------
    Typed = Table.TransformColumnTypes(
                FixPrice,
                {{"Quantity", Int64.Type}, {"UnitCost", type number}, {"DiscountPct", type number}},
                "en-GB"
            ),

    // ---- 9. Discount: blanks become 0, "10" becomes 0.10 -------------
    FixDiscount = Table.TransformColumns(
                    Typed,
                    {{"DiscountPct", each if _ = null then 0 else if _ > 1 then _ / 100 else _, type number}}
                  ),

    // ---- 10. Returned flag: Y / yes / TRUE -> "Yes", everything else "No"
    FixReturned = Table.TransformColumns(
                    FixDiscount,
                    {{"ReturnedFlag", each if List.Contains({"yes", "y", "true"}, Text.Lower(Text.Trim(_))) then "Yes" else "No", type text}}
                  ),

    // ---- 11. Fill missing prices from the same product's known price
    PriceLookup = Table.Group(FixReturned, {"Product"}, {{"RefPrice", each List.Max([UnitPrice]), type nullable number}}),
    Merged      = Table.NestedJoin(FixReturned, {"Product"}, PriceLookup, {"Product"}, "PL", JoinKind.LeftOuter),
    Expanded    = Table.ExpandTableColumn(Merged, "PL", {"RefPrice"}),
    FilledPrice = Table.AddColumn(Expanded, "UnitPriceFinal", each if [UnitPrice] = null then [RefPrice] else [UnitPrice], type number),
    DropOld     = Table.RemoveColumns(FilledPrice, {"UnitPrice", "RefPrice"}),
    RenamePrice = Table.RenameColumns(DropOld, {{"UnitPriceFinal", "UnitPrice"}}),

    // ---- 12. Remove invalid quantities (zero, negative, absurd outliers)
    ValidQty = Table.SelectRows(RenamePrice, each [Quantity] >= 1 and [Quantity] <= 20),

    // ---- 13. Calculated columns -------------------------------------
    AddRevenue = Table.AddColumn(ValidQty,    "Revenue",   each Number.Round([Quantity] * [UnitPrice] * (1 - [DiscountPct]), 2), type number),
    AddCost    = Table.AddColumn(AddRevenue,  "TotalCost", each Number.Round([Quantity] * [UnitCost], 2), type number),
    AddProfit  = Table.AddColumn(AddCost,     "Profit",    each [Revenue] - [TotalCost], type number),

    // ---- 14. Final column order and types ---------------------------
    Final = Table.TransformColumnTypes(
                Table.ReorderColumns(AddProfit, {
                    "OrderID", "OrderDate", "CustomerID", "CustomerSegment", "Region", "City",
                    "Category", "Product", "Quantity", "UnitPrice", "UnitCost", "DiscountPct",
                    "SalesChannel", "PaymentMethod", "ReturnedFlag", "Revenue", "TotalCost", "Profit"}),
                {{"OrderID", type text}, {"CustomerID", type text}}
            )
in
    Final
