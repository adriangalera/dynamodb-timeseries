import { useContext } from "react";
import { Context } from "../providers/provider";

export const useAppContext = () => {
  const context = useContext(Context);
  return {
    state: context[0],
    dispatch: context[1]
  }
};