import React, { useState } from "react";
import { fetchConfigurations, saveConfiguration } from '../api/Api';
import { useAppContext } from "./ContextHook";
import { SET_CONFIGURATIONS, ADD_CONFIGURATION, SET_API_ERROR } from "../reducers/reducer";

export const useGetConfigurations = () => {
    const { state, dispatch } = useAppContext();
    React.useEffect(() => {
        const fetchItems = async () => {
            const configurations = await fetchConfigurations();
            if (configurations === undefined) {
                dispatch({
                    type: SET_API_ERROR,
                    error: SET_CONFIGURATIONS
                });
            } else {
                dispatch({
                    type: SET_CONFIGURATIONS,
                    configurations: configurations
                });
            }
        };
        fetchItems();
    }, [dispatch]);
    const { configurations } = state;
    return configurations;
}

export const useSaveConfiguration = (defaultValues) => {
    const { dispatch } = useAppContext();
    const [inputs, setInputs] = useState(defaultValues);

    const handleSubmit = (event) => {
        if (event) {
            event.preventDefault();
        }
        const newConfiguration = {
            "aggregation_method": inputs.aggregation,
            "timezone": "Europe/Madrid",
            "retentions": {
                "hour": 16070400,
                "month": 96422400,
                "second": 259200,
                "year": 321408000,
                "day": 32140800,
                "minute": 2678400
            },
            "timeserie": inputs.timeserie
        }
        const saveConfigurationHandler = async (conf) => {
            if (conf) {
                const apiResponse = await saveConfiguration(conf);
                if (apiResponse === undefined) {
                    dispatch({
                        type: SET_API_ERROR,
                        error: ADD_CONFIGURATION
                    });
                } else {
                    dispatch({
                        type: ADD_CONFIGURATION,
                        newConfiguration: conf
                    });
                }
            }
        };
        saveConfigurationHandler(newConfiguration)
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