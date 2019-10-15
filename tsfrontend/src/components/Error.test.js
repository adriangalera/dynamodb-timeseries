import React from 'react';
import Error from './Error'
import { useAppContext } from '../hooks/ContextHook'
import { SET_CONFIGURATIONS } from '../reducers/reducer'
import { useTranslation } from 'react-i18next';
import i18n from "../i18n/i18n";

import { mount } from 'enzyme';
import Enzyme from 'enzyme';
import Adapter from 'enzyme-adapter-react-16';

Enzyme.configure({ adapter: new Adapter() });

jest.mock("../hooks/ContextHook")
jest.mock("../api/Api")

describe("Error component", () => {
    it("should not print anything when no error", () => {
        useAppContext.mockImplementation(() => {
            return {
                state: {
                    error: false
                }
            }
        })
        const wrapper = mount(<Error />)
        expect(wrapper.html()).toBe("")
    })
    it("should print error", () => {
        useAppContext.mockImplementation(() => {
            return {
                state: {
                    error: SET_CONFIGURATIONS
                }
            }
        })
        const wrapper = mount(<Error />)
        const alert = wrapper.find(".alert-danger .alert-message")
        expect(alert.text()).toBe("Error getting configuration")
    })
})