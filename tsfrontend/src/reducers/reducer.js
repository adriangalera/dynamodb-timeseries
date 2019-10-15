export const ADD_CONFIGURATION = "ADD_CONFIGURATION"
export const SET_CONFIGURATIONS = "SET_CONFIGURATIONS"
export const SET_GRAPH_DATA = "SET_GRAPH_DATA"
export const SET_API_ERROR = "SET_API_ERROR"

export const reducer = (state, action) => {
    switch (action.type) {
        case ADD_CONFIGURATION:
            return {
                ...state,
                error: false,
                configurations: [...state.configurations, {
                    ...action.newConfiguration
                }]
            };
        case SET_CONFIGURATIONS:
            return {
                ...state,
                error: false,
                configurations: action.configurations
            }
        case SET_GRAPH_DATA:
            return {
                ...state,
                error: false,
                graphData: action.graphData
            }
        case SET_API_ERROR:
            return {
                ...state,
                error: action.error,
            }
        default:
            throw new Error('Unexpected action');
    }
}