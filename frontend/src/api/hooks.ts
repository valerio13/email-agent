import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'

// Without a day it is the latest one. Moving between days keeps the previous day on screen until
// the next one arrives, so the page does not blink to a loading state.
export const useDigest = (day?: string) =>
  useQuery({
    queryKey: ['digest', day ?? 'latest'],
    queryFn: () => api.digest(day),
    placeholderData: keepPreviousData,
  })
export const useDrafts = () => useQuery({ queryKey: ['drafts'], queryFn: api.drafts })
export const useMetrics = () => useQuery({ queryKey: ['metrics'], queryFn: api.metrics })
// How the app runs does not change while it is open, so it is read once.
export const useConfig = () =>
  useQuery({ queryKey: ['config'], queryFn: api.config, staleTime: Infinity })

// Every action changes what the three views show, so each one refreshes all the queries and
// finishes only when they have loaded again. It also refreshes after a failure: a 404 or a 409
// means the screen was out of date.
function useAction<TData, TVariables = void>(action: (variables: TVariables) => Promise<TData>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: action,
    onSettled: () => queryClient.invalidateQueries(),
  })
}

export const useEditDraft = () =>
  useAction(({ id, body }: { id: number; body: string }) => api.editDraft(id, body))
export const useApproveDraft = () => useAction(api.approveDraft)
export const useDiscardDraft = () => useAction(api.discardDraft)
export const useRestoreDraft = () => useAction(api.restoreDraft)
export const useRunDemo = () => useAction(api.runDemo)
export const useResetDemo = () => useAction(api.resetDemo)
