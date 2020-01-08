import { useState } from "react";
import { fetchGraphData } from '../api/Api';
import { SET_GRAPH_DATA, SET_API_ERROR } from '../reducers/reducer';
import { useAppContext } from "./ContextHook";
import moment from 'moment'

export const processInterval = (interval) => {
    console.log(interval)
    const now = moment()
    let from, to, granularity;
    switch (interval) {
        case "last_60_seconds":
            from = moment(now).subtract(60, 'seconds').unix();
            to = now.unix();
            granularity = "second"
            return { from, to, granularity }
        case "last_5_minutes":
            from = moment(now).subtract(5, 'minutes').unix();
            to = now.unix();
            granularity = "minute"
            return { from, to, granularity }
        case "last_60_minutes":
            from = moment(now).subtract(60, 'minutes').unix();
            to = now.unix();
            granularity = "minute"
            return { from, to, granularity }            
        default:
            throw new Error('Unexpected action');
    }
}

export const useSelectorHook = (defaultValues) => {
    const { dispatch } = useAppContext();
    const [inputs, setInputs] = useState(defaultValues);

    const handleSubmit = (event) => {
        if (event.preventDefault) {
            event.preventDefault();
        }

        const queryGraphData = async (requestData) => {
            const { from, to, granularity } = processInterval(inputs.quickinternvals)
            const apiRequest = {
                timeserie: requestData.timeserie,
                start: from,
                end: to,
                granularity: granularity
            }

            const graphData = await fetchGraphData(apiRequest);
            if (graphData === undefined) {
                dispatch({
                    type: SET_API_ERROR,
                    error: SET_GRAPH_DATA
                });
            } else {
                dispatch({
                    type: SET_GRAPH_DATA,
                    graphData: graphData
                });
            }
        };
        queryGraphData(inputs)
    }

    const handleInputChange = (event) => {
        if (event.persist)
            event.persist();
        setInputs(inputs => ({ ...inputs, [event.target.name]: event.target.value }));
    }

    return {
        handleSubmit,
        handleInputChange,
        inputs
    };
}

export const useGraphData = () => {
    const { state } = useAppContext();
    const graphData = state.graphData;
    const series = []

    if (graphData) {
        for (let timeserieName of Object.keys(graphData)) {
            const millisData = graphData[timeserieName].map((data) => [data[0] * 1000, data[1]])
            const serie = {
                name: timeserieName,
                type: 'line',
                data: millisData
            }
            series.push(serie)
        }

        const graphConfiguration = {
            xAxis: {
                type: "time",
            },
            yAxis: {
                type: "value"
            },
            tooltip: {
                trigger: 'axis'
            },
            series: series
        }
        return graphConfiguration;
    }
}