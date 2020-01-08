import React from 'react';
import { useGraphData, processInterval } from "./DataHooks";
import { useAppContext } from "./ContextHook";
import { mount } from 'enzyme';
import Enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';
import moment from 'moment'

Enzyme.configure({ adapter: new Adapter() });
jest.mock("./ContextHook")
describe("Data hook", () => {
    it("should transform empty graphData into graphConfiguration", () => {
        useAppContext.mockImplementation(() => {
            return {
                state: {
                    graphData: {}
                }
            }
        })

        const graphConfiguration = useGraphData()
        const expectedGraphConfiguration = {
            xAxis: {
                type: "time",
            },
            yAxis: {
                type: "value"
            },
            tooltip: {
                trigger: 'axis'
            },            
            series: []
        }
        expect(graphConfiguration).toStrictEqual(expectedGraphConfiguration)
    })

    it("should transform one graphData into graphConfiguration", () => {
        const mockGraphData = {
            "test-timeserie": [
                [
                    1571147701,
                    62
                ], [
                    1571147712,
                    69
                ],
                [
                    1571147722,
                    -47
                ],
                [
                    1571147732,
                    60
                ],
                [
                    1571147742,
                    91
                ],
                [
                    1571147752,
                    53
                ]
            ]
        }
        useAppContext.mockImplementation(() => {
            return {
                state: {
                    graphData: mockGraphData
                }
            }
        })

        const expectedSerie = {
            name: "test-timeserie",
            type: 'line',
            data: mockGraphData["test-timeserie"].map(arr => [arr[0] * 1000, arr[1]])
        }
        const graphConfiguration = useGraphData()
        const expectedGraphConfiguration = {
            xAxis: {
                type: "time"
            },
            yAxis: {
                type: "value"
            },
            tooltip: {
                trigger: 'axis'
            },            
            series: [expectedSerie]
        }
        expect(graphConfiguration).toStrictEqual(expectedGraphConfiguration)
    })

    it("should transform one graphData into graphConfiguration", () => {
        const mockGraphData = {
            "test-timeserie": [
                [
                    1571147701,
                    62
                ], [
                    1571147712,
                    69
                ],
                [
                    1571147722,
                    -47
                ],
                [
                    1571147732,
                    60
                ],
                [
                    1571147742,
                    91
                ],
                [
                    1571147752,
                    53
                ]
            ],
            "test-timeserie-2": [
                [
                    1571147701,
                    62
                ], [
                    1571147712,
                    69
                ],
                [
                    1571147720,
                    -100
                ],
                [
                    1571147722,
                    -47
                ],
                [
                    1571147732,
                    60
                ],
                [
                    1571147742,
                    91
                ],
                [
                    1571147752,
                    53
                ]
            ]
        }
        useAppContext.mockImplementation(() => {
            return {
                state: {
                    graphData: mockGraphData
                }
            }
        })

        const expectedSerie1 = {
            name: "test-timeserie",
            type: 'line',
            data: mockGraphData["test-timeserie"].map(arr => [arr[0] * 1000, arr[1]])
        }
        const expectedSerie2 = {
            name: "test-timeserie-2",
            type: 'line',
            data: mockGraphData["test-timeserie-2"].map(arr => [arr[0] * 1000, arr[1]])
        }

        const graphConfiguration = useGraphData()
        const expectedGraphConfiguration = {
            xAxis: {
                type: "time",
            },
            yAxis: {
                type: "value"
            },
            tooltip: {
                trigger: 'axis'
            },            
            series: [expectedSerie1, expectedSerie2]
        }
        expect(graphConfiguration).toStrictEqual(expectedGraphConfiguration)
    })

    it("should process last_60_seconds", () => {
        const now = moment()
        const expectedfrom = moment(now).subtract(60, 'seconds').unix();
        const expectedto = now.unix();
        const expectedgranularity = "second"

        const { from, to, granularity } = processInterval("last_60_seconds")
        expect(from).toBe(expectedfrom)
        expect(to).toBe(expectedto)
        expect(granularity).toBe(expectedgranularity)
        expect(expectedto - expectedfrom).toBe(60)
        expect(to - from).toBe(60)
    })

})