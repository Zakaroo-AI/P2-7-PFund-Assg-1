$(document).ready(function() {
    let currentSymbol = '';
    let currentPeriod = '6mo';
    let comparePeriod = '6mo';
    let compareSymbol1 = '';
    let compareSymbol2 = '';
    
    // Initialize with a popular stock
    loadStockData('AAPL', '6mo');
    
    // Search functionality
    $('#stockSearch').on('input', function() {
        const query = $(this).val().trim();
        
        if (query.length < 1) {
            $('#autocompleteResults').hide();
            return;
        }
        
        $.getJSON('/search_stocks', { q: query }, function(data) {
            const results = $('#autocompleteResults');
            results.empty();
            
            if (data.length > 0) {
                data.forEach(function(stock) {
                    results.append('<div class="autocomplete-item" data-symbol="' + stock + '">' + stock + '</div>');
                });
                results.show();
            } else {
                results.hide();
            }
        });
    });
    
    // Compare search functionality
    $('#compareStock1, #compareStock2').on('input', function() {
        const inputId = $(this).attr('id');
        const resultsId = inputId === 'compareStock1' ? 'autocompleteResults1' : 'autocompleteResults2';
        const query = $(this).val().trim();
        
        if (query.length < 1) {
            $('#' + resultsId).hide();
            return;
        }
        
        $.getJSON('/search_stocks', { q: query }, function(data) {
            const results = $('#' + resultsId);
            results.empty();
            
            if (data.length > 0) {
                data.forEach(function(stock) {
                    results.append('<div class="autocomplete-item" data-symbol="' + stock + '" data-input="' + inputId + '">' + stock + '</div>');
                });
                results.show();
            } else {
                results.hide();
            }
        });
    });
    
    // Click on autocomplete item
    $(document).on('click', '.autocomplete-item', function() {
        const symbol = $(this).data('symbol');
        const inputId = $(this).data('input');
        
        if (inputId) {
            // This is for comparison tab
            $('#' + inputId).val(symbol);
            $('#' + (inputId === 'compareStock1' ? 'autocompleteResults1' : 'autocompleteResults2')).hide();
            
            // Update the stock info
            if (inputId === 'compareStock1') {
                compareSymbol1 = symbol;
                updateCompareStockInfo(symbol, 1);
            } else {
                compareSymbol2 = symbol;
                updateCompareStockInfo(symbol, 2);
            }
        } else {
            // This is for single stock tab
            $('#stockSearch').val(symbol);
            $('#autocompleteResults').hide();
            loadStockData(symbol, currentPeriod);
        }
    });
    
    // Search button click
    $('#searchBtn').click(function() {
        const symbol = $('#stockSearch').val().trim().toUpperCase();
        if (symbol) {
            loadStockData(symbol, currentPeriod);
        }
    });
    
    // Compare button click
    $('#compareBtn').click(function() {
        const symbol1 = $('#compareStock1').val().trim().toUpperCase();
        const symbol2 = $('#compareStock2').val().trim().toUpperCase();
        
        if (symbol1 && symbol2) {
            compareStocks(symbol1, symbol2, comparePeriod);
        } else {
            $('#compareChartError').text('Please select two stocks to compare').show();
        }
    });
    
    // Popular stock buttons
    $(document).on('click', '.stock-btn', function() {
        const symbol = $(this).data('symbol');
        const activeTab = $('.nav-link.active').attr('id');
        
        if (activeTab === 'single-tab') {
            $('#stockSearch').val(symbol);
            loadStockData(symbol, currentPeriod);
        } else if (activeTab === 'compare-tab') {
            // Determine which compare input to populate
            if (!compareSymbol1) {
                $('#compareStock1').val(symbol);
                compareSymbol1 = symbol;
                updateCompareStockInfo(symbol, 1);
            } else if (!compareSymbol2) {
                $('#compareStock2').val(symbol);
                compareSymbol2 = symbol;
                updateCompareStockInfo(symbol, 2);
            } else {
                // Both are already filled, replace the first one
                $('#compareStock1').val(symbol);
                compareSymbol1 = symbol;
                updateCompareStockInfo(symbol, 1);
            }
        }
    });
    
    // Period buttons
    $(document).on('click', '.period-btn', function() {
        $('.period-btn').removeClass('active');
        $(this).addClass('active');
        currentPeriod = $(this).data('period');
        
        if (currentSymbol) {
            loadStockData(currentSymbol, currentPeriod);
        }
    });
    
    // Compare period buttons
    $(document).on('click', '.compare-period-btn', function() {
        $('.compare-period-btn').removeClass('active');
        $(this).addClass('active');
        comparePeriod = $(this).data('period');
        
        if (compareSymbol1 && compareSymbol2) {
            compareStocks(compareSymbol1, compareSymbol2, comparePeriod);
        }
    });
    
    // Function to load stock data
    function loadStockData(symbol, period) {
        $('#loadingSpinner').show();
        $('#stockChart').hide();
        $('#chartError').hide();
        
        $.getJSON('/get_stock_data', { symbol: symbol, period: period }, function(data) {
            if (data.error) {
                $('#chartError').text(data.error).show();
                $('#loadingSpinner').hide();
                return;
            }
            
            currentSymbol = data.symbol;
            
            // Update stock info
            $('#companyName').text(data.companyName);
            $('#stockSymbol').text(data.symbol);
            $('#stockPrice').text('$' + data.currentPrice.toFixed(2));
            
            // Update change indicator
            const changeElem = $('#stockChange');
            changeElem.text((data.change >= 0 ? '+' : '') + data.change.toFixed(2) + 
                           ' (' + (data.changePercent >= 0 ? '+' : '') + data.changePercent.toFixed(2) + '%)');
            
            changeElem.removeClass('positive-change negative-change');
            if (data.change >= 0) {
                changeElem.addClass('positive-change badge');
            } else {
                changeElem.addClass('negative-change badge');
            }
            
            $('#stockInfo').show();
            
            // Load chart
            loadStockChart(symbol, period);
        }).fail(function() {
            $('#chartError').text('Error fetching stock data').show();
            $('#loadingSpinner').hide();
        });
    }
    
    // Function to load stock chart
    function loadStockChart(symbol, period) {
        $.getJSON('/get_stock_chart', { symbol: symbol, period: period }, function(data) {
            $('#loadingSpinner').hide();
            
            if (data.error) {
                $('#chartError').text(data.error).show();
                return;
            }
            
            $('#stockChart').attr('src', 'data:image/png;base64,' + data.image).show();
        }).fail(function() {
            $('#loadingSpinner').hide();
            $('#chartError').text('Error loading chart').show();
        });
    }
    
    // Function to update compare stock info
    function updateCompareStockInfo(symbol, stockNum) {
        $.getJSON('/get_stock_data', { symbol: symbol, period: comparePeriod }, function(data) {
            if (data.error) {
                return;
            }
            
            $(`#compareCompanyName${stockNum}`).text(data.companyName);
            $(`#compareStockSymbol${stockNum}`).text(data.symbol);
            $(`#compareStockPrice${stockNum}`).text('$' + data.currentPrice.toFixed(2));
            
            // Update change indicator
            const changeElem = $(`#compareStockChange${stockNum}`);
            changeElem.text((data.change >= 0 ? '+' : '') + data.change.toFixed(2) + 
                           ' (' + (data.changePercent >= 0 ? '+' : '') + data.changePercent.toFixed(2) + '%)');
            
            changeElem.removeClass('positive-change negative-change');
            if (data.change >= 0) {
                changeElem.addClass('positive-change badge');
            } else {
                changeElem.addClass('negative-change badge');
            }
            
            $(`#compareStockInfo${stockNum}`).show();
        });
    }
    
    // Function to compare stocks
    function compareStocks(symbol1, symbol2, period) {
        $('#compareLoadingSpinner').show();
        $('#compareChart').hide();
        $('#compareChartError').hide();
        
        $.getJSON('/compare_stocks', { symbol1: symbol1, symbol2: symbol2, period: period }, function(data) {
            $('#compareLoadingSpinner').hide();
            
            if (data.error) {
                $('#compareChartError').text(data.error).show();
                return;
            }
            
            // Update stock info
            $('#compareCompanyName1').text(data.companyName1);
            $('#compareStockSymbol1').text(data.symbol1);
            $('#compareStockPrice1').text('$' + data.currentPrice1.toFixed(2));
            
            const changeElem1 = $('#compareStockChange1');
            changeElem1.text((data.change1 >= 0 ? '+' : '') + data.change1.toFixed(2) + 
                           ' (' + (data.changePercent1 >= 0 ? '+' : '') + data.changePercent1.toFixed(2) + '%)');
            
            changeElem1.removeClass('positive-change negative-change');
            if (data.change1 >= 0) {
                changeElem1.addClass('positive-change badge');
            } else {
                changeElem1.addClass('negative-change badge');
            }
            
            $('#compareStockInfo1').show();
            
            $('#compareCompanyName2').text(data.companyName2);
            $('#compareStockSymbol2').text(data.symbol2);
            $('#compareStockPrice2').text('$' + data.currentPrice2.toFixed(2));
            
            const changeElem2 = $('#compareStockChange2');
            changeElem2.text((data.change2 >= 0 ? '+' : '') + data.change2.toFixed(2) + 
                           ' (' + (data.changePercent2 >= 0 ? '+' : '') + data.changePercent2.toFixed(2) + '%)');
            
            changeElem2.removeClass('positive-change negative-change');
            if (data.change2 >= 0) {
                changeElem2.addClass('positive-change badge');
            } else {
                changeElem2.addClass('negative-change badge');
            }
            
            $('#compareStockInfo2').show();
            
            // Show comparison chart
            $('#compareChart').attr('src', 'data:image/png;base64,' + data.image).show();
        }).fail(function() {
            $('#compareLoadingSpinner').hide();
            $('#compareChartError').text('Error comparing stocks').show();
        });
    }
    
    // Hide autocomplete when clicking outside
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.search-container').length) {
            $('.autocomplete-results').hide();
        }
    });
    
    // Tab change event
    $('button[data-bs-toggle="tab"]').on('shown.bs.tab', function(e) {
        // Clear compare fields when switching to single tab
        if (e.target.id === 'single-tab') {
            $('#compareStock1').val('');
            $('#compareStock2').val('');
            $('#compareStockInfo1').hide();
            $('#compareStockInfo2').hide();
            $('#compareChart').hide();
            compareSymbol1 = '';
            compareSymbol2 = '';
        }
    });

    // ============================
    // Daily Returns Feature
    // ============================
    let drPeriod = "6mo";

    // Handle period buttons
    $(document).on("click", ".dr-period-btn", function () {
        $(".dr-period-btn").removeClass("active");
        $(this).addClass("active");
        drPeriod = $(this).data("period");
    });

    // Handle button click to fetch daily returns
    $("#dailyReturnBtn").on("click", function () {
        let symbol = $("#dailyReturnStock").val().trim().toUpperCase();
        if (!symbol) return;

        $("#drLoadingSpinner").show();
        $("#drChartError").hide();
        $("#dailyReturnChart").hide();
        $("#dailyReturnTableContainer").hide();

        $.getJSON(`/daily_returns?symbol=${symbol}&period=${drPeriod}`, function (data) {
            $("#drLoadingSpinner").hide();

            if (data.error) {
                $("#drChartError").text(data.error).show();
                return;
            }

            // Show chart
            $("#dailyReturnChart").attr("src", "data:image/png;base64," + data.chart).show();

            // Fill table
            let tbody = $("#dailyReturnTableBody");
            tbody.empty();
            data.table.forEach(row => {
                tbody.append(`
                    <tr>
                        <td>${row.Date}</td>
                        <td>${row["Adj Close"]}</td>
                        <td>${row["Daily Return"]}%</td>
                    </tr>
                `);
            });
            $("#dailyReturnTableContainer").show();
        }).fail(function () {
            $("#drLoadingSpinner").hide();
            $("#drChartError").text("Error fetching daily returns").show();
        });
    });
});