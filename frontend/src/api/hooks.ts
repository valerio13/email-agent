import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'

export const useDigest = () => useQuery({ queryKey: ['digest'], queryFn: api.digest })
export const useDrafts = () => useQuery({ queryKey: ['drafts'], queryFn: api.drafts })
export const useMetrics = () => useQuery({ queryKey: ['metrics'], queryFn: api.metrics })

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
export const useRunDemo = () => useAction(api.runDemo)
export const useResetDemo = () => useAction(api.resetDemo)
