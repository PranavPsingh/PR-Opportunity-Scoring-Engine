/**
 * Client-side filtering keeps the list responsive after the user's permitted
 * client records have been loaded from the API.
 *
 * @template T extends {{company_name: string, industry: string, location: string, company_size: string}}
 * @param {T[]} clients
 * @param {{search: string, industry: string, companySize: string}} filters
 * @returns {T[]}
 */
export function filterClients(clients, filters) {
  const search = filters.search.trim().toLocaleLowerCase();
  return clients.filter((client) => {
    const matchesSearch = !search || [client.company_name, client.industry, client.location]
      .some((value) => value.toLocaleLowerCase().includes(search));
    return matchesSearch
      && (!filters.industry || client.industry === filters.industry)
      && (!filters.companySize || client.company_size === filters.companySize);
  });
}
