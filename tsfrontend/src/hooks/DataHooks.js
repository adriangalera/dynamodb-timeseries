import React, { useState } from "react";
import { fetchGraphData } from '../api/Api';
import { SET_GRAPH_DATA, SET_API_ERROR } from '../reducers/reducer';
import { useAppContext } from "./ContextHook";
import moment from 'moment'

export const processInterval = (interval, clickMoment) => {

    const now = moment()
    let from, to, granularity;
    switch (interval) {
        case "last_10_seconds":
            from = moment(clickMoment).subtract(10, 'seconds').unix();
            to = now.unix();
            granularity = "second"
            return { from, to, granularity }
        case "last_minute":
            from = moment(clickMoment).subtract(1, 'minute').unix();
            to = now.unix();
            granularity = "minute"
            return { from, to, granularity }
        case "last_hour":
            from = moment(clickMoment).subtract(1, 'hour').unix();
            to = now.unix();
            granularity = "hour"
            return { from, to, granularity }
        default:
            throw new Error('Unexpected action');
    }
}

export const useSelectorHook = (defaultValues) => {
    const { dispatch } = useAppContext();
    const [intervalId, setIntervalId] = useState(undefined)
    const [inputs, setInputs] = useState(defaultValues);
    const [clickMoment, setClickMoment] = useState(undefined)

    React.useEffect(() => {
        

        if (clickMoment === undefined) {
            return
        }

        if (intervalId) {
            clearInterval(intervalId)
            setIntervalId(undefined)
        }
        
        queryGraphData(inputs)
        setIntervalId(setInterval(() => queryGraphData(inputs), 1000))
    }, [clickMoment])

    const queryGraphData = async (requestData) => {
        const { from, to, granularity } = processInterval(inputs.quickinternvals, clickMoment)

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

    const handleSubmit = (event) => {
        if (event.preventDefault) {
            event.preventDefault();
        }
        
        setClickMoment(moment())
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
            series: series
        }
        return graphConfiguration;
    }
}