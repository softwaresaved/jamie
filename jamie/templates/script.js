d3.json('by_year.json', function(data) {
    MG.data_graphic({
        title: "Number of jobs by year",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#njobsyear',
        x_accessor: 'group',
        y_accessor: 'npos',
        brush: 'x'
    })
})
d3.json('by_year.json', function(data) {
    MG.data_graphic({
        title: "Proportion of jobs by year",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#propjobsyear',
        x_accessor: 'group',
        y_accessor: 'proportion_pos',
        brush: 'x'
    })
})
d3.json('by_month.json', function(data) {
    data = MG.convert.date(data, 'group');
    MG.data_graphic({
        title: "Number of jobs by month",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#njobsmonth',
        x_accessor: 'group',
        y_accessor: 'npos',
        brush: 'x'
    })
})
d3.json('by_month.json', function(data) {
    data = MG.convert.date(data, 'group');
    MG.data_graphic({
        title: "Proportion of jobs by month",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#propjobsmonth',
        x_accessor: 'group',
        y_accessor: 'proportion_pos',
        brush: 'x'
    })
})
d3.json('by_year.json', function(data) {
    MG.data_graphic({
        title: "Mean salary",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#meansalary',
        x_accessor: 'group',
        y_accessor: 'salary_mean_pos',
        brush: 'x'
    })
})

