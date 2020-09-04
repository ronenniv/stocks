# Stock Project

interface for updating stock details

## Description

REST API for updating stock details

## Implementation

1. define DATABASE_URL. default is sqlite:///data.db

2. define DEBUG_LEVEL. default is DEBUG

## API documentation

#### /stock/<<string:symbol>>
Methods: GET, POST, PUT, DEL<br>
Arguments: stock symbol<br>
Description: stock's operations

#### /stocks
Methods: GET<br>
Arguments: None<br>
Description: get list of all stocks

#### /position/<<string:symbol>>
Methods: GET, POST<br>
Arguments: stock symbol<br>
Description: positions operations

#### /position/<<int:symbol>>
Methods: DEL
Arguments: None<br>
Description: delete position id

#### /positions
Methods: GET<br>
Arguments: None<br>
Description: get list of all positions

#### /cash
Methods: GET, POST, PUT<br>
Arguments: None<br>
Description: cash operations
