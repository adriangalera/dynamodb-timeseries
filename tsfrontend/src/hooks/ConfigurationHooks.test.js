import React from 'react';
import { useGetConfigurations, useSaveConfiguration } from "./ConfigurationHooks";
import { fetchConfigurations, saveConfiguration } from '../api/Api';
import { useAppContext } from "./ContextHook";
import { SET_CONFIGURATIONS, ADD_CONFIGURATION, SET_API_ERROR } from "../reducers/reducer";
import { mount } from 'enzyme';
import Enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

Enzyme.configure({ adapter: new Adapter() });
jest.mock('../api/Api')
jest.mock('./ContextHook')
describe("Configuration Hooks", () => {

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

    it("should load configuration from API and invoke SET_CONFIGURATIONS action", async () => {
        const dispatchMock = jest.fn()
        useAppContext.mockImplementation(() => {
            return {
                state: { configurations: [mockConfiguration] },
                dispatch: dispatchMock
            }
        })
        fetchConfigurations.mockImplementation(() => [mockConfiguration])
        const TestComponent = () => {
            useGetConfigurations()
            return <div></div>
        }
        await mount(<TestComponent />)
        expect(fetchConfigurations).toHaveBeenCalled();
        const expectedDispatch = {
            type: SET_CONFIGURATIONS,
            configurations: [mockConfiguration]
        }
        expect(dispatchMock.mock.calls.length).toBe(1);
        expect(dispatchMock).toBeCalledWith(expectedDispatch);
    })

    it("should save configuration in API and invoke ADD_CONFIGURATION action", async () => {
        const dispatchMock = jest.fn()
        useAppContext.mockImplementation(() => {
            return {
                state: { configurations: [] },
                dispatch: dispatchMock
            }
        })
        saveConfiguration.mockImplementation(() => { return {} })
        const TestComponent = () => {
            const { inputs, handleInputChange, handleSubmit } = useSaveConfiguration({});
            return <form onSubmit={handleSubmit}>
                Name <input name="timeserie" type="text" onChange={handleInputChange} value={inputs.timeserie}></input>
                Aggregation method <select name="aggregation" onChange={handleInputChange} value={inputs.aggregation}>
                    <option value="sum">Sum</option>
                    <option value="last">Last</option>
                    <option value="max">Max</option>
                    <option value="min">Min</option>
                    <option value="average">Average</option>
                    <option value="count">Count</option>
                </select>
                <button type="submit">Save</button>
            </form>
        }
        const wrapper = mount(<TestComponent />)
        const form = wrapper.find("form")
        const tsName = wrapper.find("input")
        const aggMethodSelect = wrapper.find("select")
        const submitBtn = wrapper.find("button")
        expect(tsName.length).toBe(1)
        expect(aggMethodSelect.length).toBe(1)
        expect(submitBtn.length).toBe(1)

        tsName.simulate('change', { persist: () => { }, target: { name: 'timeserie', value: mockConfiguration.timeserie } });
        aggMethodSelect.simulate('change', { persist: () => { }, target: { name: 'aggregation', value: mockConfiguration.aggregation_method } });
        form.simulate('submit');

        await expect(saveConfiguration).toHaveBeenCalledWith(mockConfiguration)
        const expectedDispatch = {
            type: ADD_CONFIGURATION,
            newConfiguration: mockConfiguration
        }
        expect(dispatchMock.mock.calls.length).toBe(1);
        expect(dispatchMock).toBeCalledWith(expectedDispatch);
    })

    it("should invoke SET_API_ERROR when fetchConfiguration fails", async () => {
        const dispatchMock = jest.fn()
        useAppContext.mockImplementation(() => {
            return {
                state: { configurations: [mockConfiguration] },
                dispatch: dispatchMock
            }
        })
        fetchConfigurations.mockImplementation(() => undefined)
        const TestComponent = () => {
            useGetConfigurations()
            return <div></div>
        }
        await mount(<TestComponent />)
        expect(fetchConfigurations).toHaveBeenCalled();
        const expectedDispatch = {
            type: SET_API_ERROR,
            error: SET_CONFIGURATIONS
        }
        expect(dispatchMock.mock.calls.length).toBe(1);
        expect(dispatchMock).toBeCalledWith(expectedDispatch);
    })

    it("should invoke SET_API_ERROR when saveConfiguration fails", async () => {
        const dispatchMock = jest.fn()
        useAppContext.mockImplementation(() => {
            return {
                state: { configurations: [] },
                dispatch: dispatchMock
            }
        })
        saveConfiguration.mockImplementation(() => undefined)
        const TestComponent = () => {
            const { inputs, handleInputChange, handleSubmit } = useSaveConfiguration({});
            return <form onSubmit={handleSubmit}>
                Name <input name="timeserie" type="text" onChange={handleInputChange} value={inputs.timeserie}></input>
                Aggregation method <select name="aggregation" onChange={handleInputChange} value={inputs.aggregation}>
                    <option value="sum">Sum</option>
                    <option value="last">Last</option>
                    <option value="max">Max</option>
                    <option value="min">Min</option>
                    <option value="average">Average</option>
                    <option value="count">Count</option>
                </select>
                <button type="submit">Save</button>
            </form>
        }
        const wrapper = mount(<TestComponent />)
        const form = wrapper.find("form")
        const tsName = wrapper.find("input")
        const aggMethodSelect = wrapper.find("select")
        const submitBtn = wrapper.find("button")
        expect(tsName.length).toBe(1)
        expect(aggMethodSelect.length).toBe(1)
        expect(submitBtn.length).toBe(1)

        tsName.simulate('change', { persist: () => { }, target: { name: 'timeserie', value: mockConfiguration.timeserie } });
        aggMethodSelect.simulate('change', { persist: () => { }, target: { name: 'aggregation', value: mockConfiguration.aggregation_method } });
        form.simulate('submit');

        await expect(saveConfiguration).toHaveBeenCalledWith(mockConfiguration)
        const expectedDispatch = {
            type: SET_API_ERROR,
            error: ADD_CONFIGURATION
        }
        expect(dispatchMock.mock.calls.length).toBe(1);
        expect(dispatchMock).toBeCalledWith(expectedDispatch);
    })
})