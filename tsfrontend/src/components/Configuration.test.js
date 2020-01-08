import React from 'react';
import { ConfigurationTable, formatRetention, ConfigurationEntry, NewConfigurationForm, Configuration } from './Configuration'
import { saveConfiguration } from '../api/Api'
import { ADD_CONFIGURATION } from '../reducers/reducer'
import { useAppContext } from '../hooks/ContextHook'
import { shallow, mount } from 'enzyme';
import Enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

Enzyme.configure({ adapter: new Adapter() });
jest.mock("../hooks/ContextHook")
jest.mock("../api/Api")

describe("Configuration component tests", () => {
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
    const headers = ["Timeserie name", "Aggregation method", "TTL (second)",
        "TTL (minute)", "TTL (hour)", "TTL (day)", "TTL (month)", "TTL (year)", "Timezone"]



    test('should format retention', () => {
        const retention = 300;
        const fmtRetention = formatRetention(retention)
        expect(fmtRetention).toBe(retention)
    });

    test('should create configuration table entry', () => {
        const wrapper = shallow(ConfigurationEntry(mockConfiguration))
        const tr = wrapper.find("tr")
        const td = wrapper.find("td")
        expect(tr.key()).toBe(mockConfiguration["timeserie"])
        expect(tr.length).toBe(1)
        expect(td.length).toBe(9)

        expect(td.at(0).text()).toBe(mockConfiguration["timeserie"])
        expect(td.at(1).text()).toBe(mockConfiguration["aggregation_method"])

        expect(parseInt(td.at(2).text())).toBe(formatRetention(mockConfiguration["retentions"]["second"]))
        expect(parseInt(td.at(3).text())).toBe(formatRetention(mockConfiguration["retentions"]["minute"]))
        expect(parseInt(td.at(4).text())).toBe(formatRetention(mockConfiguration["retentions"]["hour"]))
        expect(parseInt(td.at(5).text())).toBe(formatRetention(mockConfiguration["retentions"]["day"]))
        expect(parseInt(td.at(6).text())).toBe(formatRetention(mockConfiguration["retentions"]["month"]))
        expect(parseInt(td.at(7).text())).toBe(formatRetention(mockConfiguration["retentions"]["year"]))

        expect(td.at(8).text()).toBe(mockConfiguration["timezone"])
    })

    test('should create table', () => {
        const wrapper = mount(ConfigurationTable({ 'configurations': [mockConfiguration] }))
        const table = wrapper.find("table")
        expect(table.length).toBe(1)
        const tableHeadColums = wrapper.find("thead tr td")
        headers.map((header, index) => expect(tableHeadColums.at(index).text()).toBe(header))
    })

    test('should create new configuration', async () => {
        const mockedDispatch = jest.fn()
        saveConfiguration.mockImplementation(() => { return {} })
        useAppContext.mockImplementation(() => {
            return {
                dispatch: mockedDispatch
            }
        })

        const wrapper = mount(<NewConfigurationForm />);
        const form = wrapper.find("form")
        const tsName = wrapper.find("input")
        const aggMethodSelect = wrapper.find("select")
        const submitBtn = wrapper.find("button")
        expect(tsName.length).toBe(1)
        expect(aggMethodSelect.length).toBe(1)
        expect(submitBtn.length).toBe(1)

        const newConfiguration = {
            "aggregation_method": "last",
            "timezone": "Europe/Madrid",
            "retentions": {
                "hour": 16070400,
                "month": 96422400,
                "second": 259200,
                "year": 321408000,
                "day": 32140800,
                "minute": 2678400
            },
            "timeserie": "timeserie-name-new"
        }

        tsName.simulate('change', { persist: () => { }, target: { name: 'timeserie', value: newConfiguration.timeserie } });
        aggMethodSelect.simulate('change', { persist: () => { }, target: { name: 'aggregation', value: newConfiguration.aggregation_method } });
        form.simulate('submit');
        await expect(saveConfiguration).toHaveBeenCalled()
        const expectedDispatch = {
            "newConfiguration": newConfiguration,
            "type": ADD_CONFIGURATION
        }
        expect(mockedDispatch).toHaveBeenCalledWith(expectedDispatch)
    })

    test('should load configuration from API', () => {
        useAppContext.mockImplementation(() => {
            return {
                state: {
                    configurations: [mockConfiguration]
                }
            }
        })
        const wrapper = mount(<Configuration />)
        const table = wrapper.find(ConfigurationTable)
        const form = wrapper.find(NewConfigurationForm)
        expect(table.props().configurations.length).toBe(1)
        expect(table.length).toBe(1)
        expect(form.length).toBe(1)
        expect(wrapper.find("tbody tr td").length).toBe(9)
    })
})

