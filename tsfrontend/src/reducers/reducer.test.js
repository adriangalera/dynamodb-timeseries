import { ADD_CONFIGURATION, SET_CONFIGURATIONS, reducer, SET_API_ERROR } from './reducer'

describe("Configuration tests", () => {
  const mockConfiguration = {
    "aggregation_method": "sum",
    "timezone": "Europe/Madrid",
    "retentions": {
      "hour": 16070400,
      "month": 96422400,
      "second": 259200,
      "year": 321408000,
      "day": 32140800,
      "minute": 2678400
    },
    "timeserie": "timeserie-mocked-name"
  }
  it("should add new configuration in empty state", () => {
    const state = {
      configurations: [],
      error: false
    }
    const newState = reducer(state, {
      type: ADD_CONFIGURATION,
      newConfiguration: mockConfiguration
    })
    expect(newState.configurations.length).toBe(1)
    expect(newState.configurations[0]).toEqual(mockConfiguration)
    expect(newState.error).toBe(false)
  })
  it("should add new configuration in non empty state", () => {
    const state = {
      configurations: [mockConfiguration],
      error: false
    }
    const newState = reducer(state, {
      type: ADD_CONFIGURATION,
      newConfiguration: mockConfiguration
    })
    expect(newState.configurations.length).toBe(2)
    expect(newState.configurations[0]).toEqual(mockConfiguration)
    expect(newState.configurations[1]).toEqual(mockConfiguration)
    expect(newState.error).toBe(false)
  })
  it("should set configurations in empty state", () => {
    const state = {
      configurations: [],
      error: false
    }
    const newState = reducer(state, {
      type: SET_CONFIGURATIONS,
      configurations: [mockConfiguration]
    })
    expect(newState.configurations.length).toBe(1)
    expect(newState.configurations[0]).toEqual(mockConfiguration)
    expect(newState.error).toBe(false)
  })
  it("should set configurations in non empty state", () => {
    const state = {
      configurations: [],
      error: false
    }
    const newState = reducer(state, {
      type: SET_CONFIGURATIONS,
      configurations: [mockConfiguration]
    })
    expect(newState.configurations.length).toBe(1)
    expect(newState.configurations[0]).toEqual(mockConfiguration)
    expect(newState.error).toBe(false)
  })
  it("should reset error on successful operation", () => {
    const state = {
      configurations: [],
      error: true
    }
    const newState = reducer(state, {
      type: SET_CONFIGURATIONS,
      configurations: [mockConfiguration]
    })
    expect(newState.configurations.length).toBe(1)
    expect(newState.configurations[0]).toEqual(mockConfiguration)
    expect(newState.error).toBe(false)
  })
  it("should set error to dispatched event", () => {
    const state = {
      error: false
    }
    const newState = reducer(state, {
      type: SET_API_ERROR,
      error: SET_CONFIGURATIONS
    })
    expect(newState.error).not.toBe(false)
    expect(newState.error).toBe(SET_CONFIGURATIONS)
  })
})