

// line chart 

const xVals = ['2023-10-25', '2023-11-07', '2023-12-06',
    '2024-02-20', '2024-04-12', '2024-04-17',
    '2024-04-22', '2024-04-23', '2024-04-26', '2024-05-07'];

const yVals = [7, 5.5, 3, 1, 3, 2, 1, 5, 1, 2];


const myChart = new Chart ("myChart", {
    type: "line",
    data: {
        labels: xVals,

        datasets: [{
            data: yVals
        }]
    },
    options: {}
});



