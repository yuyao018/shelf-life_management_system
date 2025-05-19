export default {
	logout_buttononClick () {
		removeValue('name');
		removeValue('email');
  	removeValue('user_role');
		removeValue('user_id')
  	navigateTo('Login', { replace: true });
		showAlert("Logout Successful!", "success");
	}
}