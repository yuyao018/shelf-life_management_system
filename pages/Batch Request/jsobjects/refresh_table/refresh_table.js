export default {
  async submit_buttononClick() {
		get_all_data_user.run();
		resetWidget("approval_status_select");
		resetWidget("status_select");
  }
}
