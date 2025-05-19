export default {
	async manage_batch_buttononClick () {
		await resetWidget("approval_status_select");
		await resetWidget("status_select");
		
		const role = appsmith.store.user_role;
    if (role === "admin" || role === "tester") {
      await storeValue("view_part", "all_request");
			get_all_data_admin.run();
    } else if (role === "owner") {
      await storeValue("view_part", "my_request");
			get_all_data_user.run();
    }
		navigateTo("Batch Request")
	}
}