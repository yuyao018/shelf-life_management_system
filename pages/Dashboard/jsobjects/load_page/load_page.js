export default {
	manage_batch_buttononClick () {
		const role = appsmith.store.user_role;
    if (role === "admin" || role === "tester") {
      storeValue("view_part", "all_request");
    } else if (role === "owner") {
      storeValue("view_part", "my_request");
    }
		navigateTo("Batch Request")
	}
}