// Returns item indices sorted chronologically by date (then time as a
// tiebreaker), so callers can render in sorted order while still using the
// original index for onUpdate/onRemove — the underlying array itself is
// left untouched.
//
// `indices` optionally restricts the result to a subset of `items`, which is
// how a tab renders one category (e.g. only tasks whose task_type is project)
// while still addressing the full array by its real indices.
export function getSortedIndices(items, dateField, timeField, indices) {
  return (indices ?? items.map((_, index) => index))
    .slice()
    .sort((a, b) => {
      const dateA = items[a][dateField];
      const dateB = items[b][dateField];
      if (dateA !== dateB) {
        if (!dateA) return 1;
        if (!dateB) return -1;
        return dateA < dateB ? -1 : 1;
      }

      const timeA = items[a][timeField];
      const timeB = items[b][timeField];
      if (timeA === timeB) return 0;
      if (!timeA) return -1;
      if (!timeB) return 1;
      return timeA < timeB ? -1 : 1;
    });
}
