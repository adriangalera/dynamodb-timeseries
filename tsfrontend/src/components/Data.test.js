import React from 'react';
import {
    extractTimeseriesFromConfiguration, Selectors
} from './Data'
import { SET_GRAPH_DATA, SET_API_ERROR } from '../reducers/reducer'
import { fetchGraphData } from '../api/Api'
import { useAppContext } from '../hooks/ContextHook'
import { shallow, mount } from 'enzyme';
import Enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

Enzyme.configure({ adapter: new Adapter() });

jest.mock("../hooks/ContextHook")
jest.mock("../api/Api")
jest.useFakeTimers();


describe("Data component", () => {

    const mockConfiguration1 = {
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

    const mockConfiguration2 = {
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
        "timeserie": "timeserie-mocked-name-2"
    }

    const generateMockGraphData = (timeserie, timeadd = 0) => {
        return {
            timeserie: [
                [
                    1571147701 + timeadd,
                    62
                ], [
                    1571147712 + timeadd,
                    69
                ],
                [
                    1571147722 + timeadd,
                    -47
                ],
                [
                    1571147732 + timeadd,
                    60
                ],
                [
                    1571147742 + timeadd,
                    91
                ],
                [
                    1571147752 + timeadd,
                    53
                ]
            ]
        }
    }

    const mockedDispatch = jest.fn()
    useAppContext.mockImplementation(() => {
        return {
            state: {
                configurations: [mockConfiguration1, mockConfiguration2]
            },
            dispatch: mockedDispatch
        }
    })

    it("should extract timeseries names", () => {
        const timeseries = extractTimeseriesFromConfiguration([mockConfiguration1, mockConfiguration2])
        expect(timeseries).toStrictEqual([mockConfiguration1.timeserie, mockConfiguration2.timeserie])
    })

    it("Selector should populate timeseries selector from configuration", () => {
        const selector = mount(<Selectors />)
        const selectorOptions = selector.find(`select[name='timeserie'] option`).map(op => op.text())
        expect(selectorOptions.length).toBe(2)
        expect(selectorOptions).toStrictEqual([mockConfiguration1.timeserie, mockConfiguration2.timeserie])
    })

    it("should trigger GET /data call on form submit", async () => {
        const mockGraphData = generateMockGraphData(mockConfiguration1.timeserie)
        fetchGraphData.mockImplementation(() => mockGraphData)
        const selector = mount(<Selectors />)
        const form = selector.find("form")
        const timeseriesSelect = selector.find("select[name='timeserie']")
        //const from = selector.find("input[name='from']")
        //const to = selector.find("input[name='to']")
        //const granularitySelect = selector.find("select[name='granularity']")
        const intervalsSelect = selector.find("select[name='quickinternvals']")

        expect(timeseriesSelect.length).toBe(1)
        //expect(from.length).toBe(1)
        //expect(to.length).toBe(1)
        //expect(granularitySelect.length).toBe(1)
        expect(intervalsSelect.length).toBe(1)

        timeseriesSelect.simulate('change', { persist: () => { }, target: { name: 'timeserie', value: mockConfiguration1.timeserie } });
        //from.simulate('change', { persist: () => { }, target: { name: 'from', value: "0" } });
        //to.simulate('change', { persist: () => { }, target: { name: 'to', value: "1000" } });
        //granularitySelect.simulate('change', { persist: () => { }, target: { name: 'granularity', value: "second" } });
        intervalsSelect.simulate('change', { persist: () => { }, target: { name: 'quickinternvals', value: "last_60_seconds" } });
        form.simulate('submit');

        const expectedDispatch = {
            type: SET_GRAPH_DATA,
            graphData: mockGraphData
        }

        await expect(fetchGraphData).toHaveBeenCalled();
        expect(mockedDispatch).toBeCalledWith(expectedDispatch)
    })

    it("should invoke SET_API_ERROR", async () => {
        fetchGraphData.mockImplementation(() => undefined)
        const selector = mount(<Selectors />)
        const form = selector.find("form")
        const timeseriesSelect = selector.find("select[name='timeserie']")
        //const from = selector.find("input[name='from']")
        //const to = selector.find("input[name='to']")
        //const granularitySelect = selector.find("select[name='granularity']")
        const intervalsSelect = selector.find("select[name='quickinternvals']")

        expect(timeseriesSelect.length).toBe(1)
        //expect(from.length).toBe(1)
        //expect(to.length).toBe(1)
        //expect(granularitySelect.length).toBe(1)

        timeseriesSelect.simulate('change', { persist: () => { }, target: { name: 'timeserie', value: mockConfiguration1.timeserie } });
        //from.simulate('change', { persist: () => { }, target: { name: 'from', value: "0" } });
        //to.simulate('change', { persist: () => { }, target: { name: 'to', value: "1000" } });
        intervalsSelect.simulate('change', { persist: () => { }, target: { name: 'quickinternvals', value: "last_60_seconds" } });

        form.simulate('submit');

        const expectedDispatch = {
            type: SET_API_ERROR,
            error: SET_GRAPH_DATA
        }

        await expect(fetchGraphData).toHaveBeenCalled();
        expect(mockedDispatch).toBeCalledWith(expectedDispatch)
    })

    it("should invoke setInterval when searching", async () => {
        const mockGraphData = generateMockGraphData(mockConfiguration1.timeserie)
        fetchGraphData.mockImplementation(() => mockGraphData)
        const selector = mount(<Selectors />)
        const form = selector.find("form")
        const timeseriesSelect = selector.find("select[name='timeserie']")
        const intervalsSelect = selector.find("select[name='quickinternvals']")

        expect(timeseriesSelect.length).toBe(1)
        expect(intervalsSelect.length).toBe(1)

        timeseriesSelect.simulate('change', { persist: () => { }, target: { name: 'timeserie', value: mockConfiguration1.timeserie } });
        intervalsSelect.simulate('change', { persist: () => { }, target: { name: 'quickinternvals', value: "last_10_seconds" } });
        form.simulate('submit');

        const expectedDispatch = {
            type: SET_GRAPH_DATA,
            graphData: mockGraphData
        }

        await expect(fetchGraphData).toHaveBeenCalled();
        expect(mockedDispatch).toBeCalledWith(expectedDispatch)
        jest.advanceTimersByTime(1000);
        await expect(fetchGraphData).toHaveBeenCalled();
        expect(mockedDispatch).toBeCalledWith(expectedDispatch)

    })
})