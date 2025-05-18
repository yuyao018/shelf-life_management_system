export default {
	status_selectonOptionChange () {
		const role = appsmith.store.user_role;
		if(role === "user"){
			get_all_data_user.run()
		} else if (role === "admin" || role === "tester"){
			get_all_data_admin.run()
		}
	}
}