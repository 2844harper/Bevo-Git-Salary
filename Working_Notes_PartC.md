# Working Notes
Cleaned the GDP and income data, keeping county-level observations from 2010–2024.

Calculated annual growth rates, 10-year average growth rates, and CAGR.

Used the HUD ZIP–County crosswalk to assign County FIPS codes to schools. For ZIP codes covering multiple counties, I selected the county with the highest address ratio.

Manually assigned FIPS codes to 9 schools that couldn't be matched automatically.

Merged the GDP and income data into Scorecard using County FIPS.

# Results
Out of 1,162 schools, 1,119 were successfully matched with both economic datasets. The remaining 43 are mainly in Virginia and U.S. territories.

# Suggestion 
I suggest documenting these 43 unmatched schools and excluding them from our final regression analysis. We can then discuss this data limitation and its potential impact on our results in the reflection section.