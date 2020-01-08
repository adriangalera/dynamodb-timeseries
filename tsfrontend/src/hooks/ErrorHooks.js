import { useAppContext } from "./ContextHook";

export const useGetError = () => {
    const { state } = useAppContext();
    return state.error
}